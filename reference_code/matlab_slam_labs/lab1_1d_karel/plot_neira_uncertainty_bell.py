#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot_neira_uncertainty_bell.py
==============================
Deconstrucción visual y matemática de la construcción gráfica de José Neira y Juan D. Tardós:
"La campana de incertidumbre que se abre a cada paso (y por qué Neira la pone al revés)".

Basado estrictamente en:
- Karel 1D: T#8_LAB1_Complete.m (Líneas 455-471 y 496-511)
- Karel 2D: show_results.m (Líneas 33-51)
- Transparencias de Lección 1 (Diapositivas 9, 13, 14, 15, 24, 51, 52, 58)
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt

def generate_neira_plots(output_path):
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['mathtext.fontset'] = 'cm'

    fig = plt.figure(figsize=(15, 12), dpi=180)
    gs = fig.add_gridspec(3, 1, height_ratios=[1.0, 1.25, 1.15], hspace=0.38)

    # =========================================================================
    # SUBPLOT 1: Visión Estadística Convencional (Campanas Verticales p(x))
    # =========================================================================
    ax1 = fig.add_subplot(gs[0])
    x_axis = np.linspace(-1, 22, 2500)
    u_step = 1.0
    sigma_u = 0.25
    steps = [1, 3, 6, 11, 18]
    colors = plt.cm.plasma(np.linspace(0.15, 0.85, len(steps)))

    for k, c in zip(steps, colors):
        mu_k = k * u_step
        sigma_k = np.sqrt(k) * sigma_u
        pdf = (1.0 / (sigma_k * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_axis - mu_k) / sigma_k)**2)
        ax1.plot(x_axis, pdf, color=c, lw=2.2, label=f'Paso k={k:02d} (mu={mu_k:.0f}m, sigma={sigma_k:.2f}m)')
        ax1.fill_between(x_axis, 0, pdf, color=c, alpha=0.15)
        ax1.vlines(mu_k, 0, 1.0 / (sigma_k * np.sqrt(2 * np.pi)), color=c, linestyle=':', alpha=0.7)

    ax1.set_title(
        '1. Vision Estadistica Convencional: Campanas Verticales de Densidad p(x_k)\n'
        'A cada paso la campana avanza a la derecha, su anchura se abre (sigma ~ sqrt(k)) y su altura se aplana (p_max ~ 1/sqrt(k))',
        fontsize=11, fontweight='bold', pad=8
    )
    ax1.set_xlabel('Posicion Absoluta del Robot X (metros)', fontsize=10, fontweight='bold')
    ax1.set_ylabel('Densidad de Probabilidad p(x)', fontsize=10, fontweight='bold')
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend(loc='upper right', fontsize=8.5, framealpha=0.9)
    ax1.set_xlim(-0.5, 21.5)
    ax1.set_ylim(0, 1.7)

    # =========================================================================
    # SUBPLOT 2: La Campana 'Al Reves' de Neira (Envolvente Horizontal +-2sigma)
    # =========================================================================
    ax2 = fig.add_subplot(gs[1])
    np.random.seed(42)
    N_steps = 1000
    k_vec = np.arange(1, N_steps + 1)
    noise_sigma = 0.1 # sigma_u = 0.1m

    # Generar odometria ruidosa (random walk browniano)
    noise_steps = np.random.normal(0, noise_sigma, N_steps)
    error_odom = np.cumsum(noise_steps) # e_k = true - estimated
    sigma_odom = noise_sigma * np.sqrt(k_vec)

    # SLAM con Loop Closure en el paso 600
    error_slam = np.copy(error_odom)
    sigma_slam = np.copy(sigma_odom)

    for i in range(600, N_steps):
        ratio = (i - 600) / 400.0
        sigma_slam[i] = 0.12 + (1.0 - ratio) * 0.08
        error_slam[i] = error_slam[600] * (1.0 - ratio) * 0.15 + np.random.normal(0, sigma_slam[i] * 0.4)

    # Cotas Neira Odometria (+-2 sigma)
    ax2.plot(k_vec, 2 * sigma_odom, 'b-', lw=2.2, label=r'Cota Superior Neira: $+2\sigma_k$ (T#8_LAB1_Complete.m L506)')
    ax2.plot(k_vec, -2 * sigma_odom, 'b-', lw=2.2, label=r'Cota Inferior Neira: $-2\sigma_k$ (T#8_LAB1_Complete.m L507)')
    ax2.fill_between(k_vec, -2 * sigma_odom, 2 * sigma_odom, color='blue', alpha=0.08)

    # Error real de odometria (rojo, como en LAB1 L505)
    ax2.plot(k_vec, error_odom, 'r-', lw=1.6, alpha=0.85, label='Error Odometria: x_{true} - x_{hat} (LAB1 L505)')

    # SLAM con Loop Closure
    ax2.plot(k_vec[600:], 2 * sigma_slam[600:], 'm--', lw=2.4, label=r'SLAM Loop Closure: $\pm 2\sigma$ colapsa bruscamente')
    ax2.plot(k_vec[600:], -2 * sigma_slam[600:], 'm--', lw=2.4)
    ax2.plot(k_vec[600:], error_slam[600:], 'k-', lw=1.6, label='Error SLAM post-cierre de bucle')
    ax2.fill_between(k_vec[600:], -2 * sigma_slam[600:], 2 * sigma_slam[600:], color='magenta', alpha=0.22)

    ax2.axhline(0, color='gray', linestyle=':', lw=1.2)
    ax2.set_title(
        '2. La Campana "Al Reves" de Neira: Envolvente Horizontal de Error y Cotas +-2sigma (Karel 1D)\n'
        'Neira acuesta la campana a 90 grados: el eje horizontal es la distancia/pasos y el eje vertical es el error de estimacion.\n'
        'La boca de la campana SE ABRE a cada paso (+-2*sigma_u*sqrt(k)). Al cerrar bucle, ¡la campana se cierra de golpe!',
        fontsize=11, fontweight='bold', pad=8
    )
    ax2.set_xlabel('Distancia Recorrida / Pasos k (metros)', fontsize=10, fontweight='bold')
    ax2.set_ylabel('Error e_k = x_true - x_hat (m)', fontsize=10, fontweight='bold')
    ax2.grid(True, linestyle='--', alpha=0.5)
    ax2.legend(loc='lower left', fontsize=8.5, framealpha=0.9, ncol=2)
    ax2.set_xlim(0, 1000)
    ax2.set_ylim(-7.5, 7.5)

    ax2.annotate(
        'Boca de la campana abriendose:\nsigma(k) = sigma_u * sqrt(k) -> inf (Odometria)',
        xy=(500, 2 * sigma_odom[500]), xytext=(280, 5.2),
        arrowprops=dict(facecolor='blue', shrink=0.08, width=1.5, headwidth=6),
        fontsize=9, fontweight='bold', color='blue',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#e6f0ff', edgecolor='blue')
    )

    ax2.annotate(
        'Cierre de Bucle (Paso 600):\nColapso total de la campana (Neira P58)',
        xy=(605, 2 * sigma_slam[605]), xytext=(650, 4.8),
        arrowprops=dict(facecolor='magenta', shrink=0.08, width=1.5, headwidth=6),
        fontsize=9, fontweight='bold', color='magenta',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffe6ff', edgecolor='magenta')
    )

    # =========================================================================
    # SUBPLOT 3: Consistencia vs Inconsistencia (Neira en 2D: show_results.m)
    # =========================================================================
    ax3 = fig.add_subplot(gs[2])
    steps_2d = 180
    k_2d = np.arange(1, steps_2d + 1)
    chi2_val = 6.635 # chi2(1) al 99%

    # Covarianza EKF consistente (JCBB)
    sigma_jcbb = 0.08 + 0.02 * np.sqrt(k_2d)
    sigma_jcbb[120:] = 0.05 # Loop closure at step 120
    bound_jcbb = np.sqrt(chi2_val) * sigma_jcbb
    error_jcbb = np.random.normal(0, sigma_jcbb * 0.45)
    error_jcbb = np.clip(error_jcbb, -0.85 * bound_jcbb, 0.85 * bound_jcbb)

    # Covarianza EKF inconsistente (NN con falsa asociacion)
    sigma_nn_optimistic = 0.08 + 0.015 * np.sqrt(k_2d)
    bound_nn = np.sqrt(chi2_val) * sigma_nn_optimistic
    error_nn_divergent = np.copy(error_jcbb)
    error_nn_divergent[70:] = error_nn_divergent[70] + 0.03 * (k_2d[70:] - 70)**1.3

    ax3.plot(k_2d, bound_jcbb, 'r-', lw=2.0, label=r'Cota Consistente JCBB: $+\sqrt{\chi^2_1 \cdot P_{xx}}$ (show_results.m L37)')
    ax3.plot(k_2d, -bound_jcbb, 'r-', lw=2.0, label=r'Cota Consistente JCBB: $-\sqrt{\chi^2_1 \cdot P_{xx}}$ (show_results.m L38)')
    ax3.plot(k_2d, error_jcbb, 'b-', lw=1.6, label='Error Real JCBB (Consistente: confinado dentro de la campana)')

    ax3.plot(k_2d, error_nn_divergent, 'k--', lw=2.2, label='Error Real NN (INCONSISTENTE: rompe la campana y diverge)')
    ax3.fill_between(k_2d, -bound_jcbb, bound_jcbb, color='green', alpha=0.10)

    ax3.set_title(
        '3. Prueba de Consistencia de Neira en 2D (show_results.m): JCBB vs Nearest Neighbor (NN)\n'
        'Un estimador es CONSISTENTE si y solo si el error real se mantiene dentro de las cotas el 99% del tiempo.\n'
        'Si una asociacion erronea entra al filtro (NN), la incertidumbre teorica se encoge pero el error real escapa de la campana.',
        fontsize=11, fontweight='bold', pad=8
    )
    ax3.set_xlabel('Paso de Simulacion 2D (k)', fontsize=10, fontweight='bold')
    ax3.set_ylabel('Error en x: g(1) - e(1) (m)', fontsize=10, fontweight='bold')
    ax3.grid(True, linestyle='--', alpha=0.5)
    ax3.legend(loc='upper left', fontsize=8.5, framealpha=0.9, ncol=2)
    ax3.set_xlim(0, steps_2d)
    ax3.set_ylim(-1.6, 2.5)

    ax3.annotate(
        'Fallo de Asociacion en NN:\nEl error escapa de la campana -> Inconsistencia',
        xy=(110, error_nn_divergent[110]), xytext=(95, 1.8),
        arrowprops=dict(facecolor='black', shrink=0.08, width=1.5, headwidth=6),
        fontsize=9, fontweight='bold', color='black',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffdddd', edgecolor='red')
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=180, bbox_inches='tight')
    print('Grafica guardada con exito en:', output_path)

if __name__ == '__main__':
    out_file = r'D:\Voyager\documentation\slam_and_vision\images\neira_uncertainty_bell_and_error.png'
    generate_neira_plots(out_file)
