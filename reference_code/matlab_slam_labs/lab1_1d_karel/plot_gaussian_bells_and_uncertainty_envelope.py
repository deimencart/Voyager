#!/usr/bin/env python3
"""
Generador de la Gráfica de Campanas Gaussianas de Odometría 1D y la Trompeta de Incertidumbre (+-2 sigma).
Basado en la Lección 1 del curso de SLAM (Universidad de Zaragoza, Prof. Juan D. Tardós).
"""

import numpy as np
import matplotlib.pyplot as plt

def generate_plot(output_path="gaussian_bells_and_uncertainty_envelope.png"):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 9), dpi=150)

    # --- SUBPLOT 1: Las campanas de Gauss que se aplanan y abren con cada paso ---
    x_axis = np.linspace(-1, 20, 2000)
    u_step = 1.0       # 1 metro por paso
    sigma_u = 0.3      # Desviacion estandar de odometria por paso

    steps_to_plot = [1, 2, 4, 7, 11, 16]
    colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(steps_to_plot)))

    for k, c in zip(steps_to_plot, colors):
        mu_k = k * u_step
        sigma_k = np.sqrt(k) * sigma_u
        pdf_k = (1.0 / (sigma_k * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_axis - mu_k) / sigma_k)**2)
        ax1.plot(x_axis, pdf_k, label=f'Paso k={k}: $\mu={mu_k:.0f}m, \sigma={sigma_k:.2f}m$', color=c, lw=2.2)
        ax1.fill_between(x_axis, 0, pdf_k, color=c, alpha=0.15)
        ax1.vlines(mu_k, 0, 1.0/(sigma_k * np.sqrt(2*np.pi)), color=c, linestyle='--', alpha=0.6)

    ax1.set_title('1. Evolución de la Campana de Densidad de Probabilidad p(x_k) en Odometría 1D\n(Con cada paso la campana se desplaza, se ensancha en anchura $\propto \sqrt{k}$ y se aplana en altura $\propto 1/\sqrt{k}$)', fontsize=12, fontweight='bold', pad=10)
    ax1.set_xlabel('Posición en el mundo X (metros)', fontsize=10, fontweight='bold')
    ax1.set_ylabel('Densidad de Probabilidad p(x)', fontsize=10, fontweight='bold')
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='upper right', framealpha=0.9, fontsize=9)
    ax1.set_xlim(-0.5, 19)
    ax1.set_ylim(0, 1.5)

    # --- SUBPLOT 2: La Trompeta de Incertidumbre (+-2 sigma) Odometría vs SLAM Loop Closure ---
    total_steps = 200
    k_vec = np.arange(1, total_steps + 1)

    # Trayectoria: Avanza 100m y regresa 100m hacia el origen
    u_nominal = np.ones(total_steps)
    u_nominal[100:] = -1.0 # Da la vuelta en el paso 100
    true_pos = np.cumsum(u_nominal)

    # Odometría Pura: la incertidumbre SIEMPRE crece monótonamente (sigma = sqrt(k) * sigma_u)
    sigma_odom = np.sqrt(k_vec) * sigma_u
    env_upper_odom = true_pos + 2 * sigma_odom
    env_lower_odom = true_pos - 2 * sigma_odom

    # SLAM con Cierre de Bucle:
    sigma_slam = np.copy(sigma_odom)
    for i in range(100, total_steps):
        ratio = (i - 100) / 100.0
        sigma_slam[i] = 0.15 + (1.0 - ratio) * 0.05 + ratio * 0.1

    env_upper_slam = true_pos + 2 * sigma_slam
    env_lower_slam = true_pos - 2 * sigma_slam

    ax2.plot(k_vec, true_pos, 'k--', lw=2, label='Posición Real / Esperada $\hat{x}_k$ (Ida y Vuelta)')
    # Odometria
    ax2.plot(k_vec, env_upper_odom, 'r-', lw=1.8, label='Odometría Pura: Banda Superior $+2\sigma$ (Crece Siempre)')
    ax2.plot(k_vec, env_lower_odom, 'r-', lw=1.8, label='Odometría Pura: Banda Inferior $-2\sigma$')
    ax2.fill_between(k_vec, env_lower_odom, env_upper_odom, color='red', alpha=0.12)

    # SLAM Loop Closure
    ax2.plot(k_vec[100:], env_upper_slam[100:], 'b-', lw=2, label='SLAM con Cierre de Bucle (Paso 100: Colapso de Incertidumbre)')
    ax2.plot(k_vec[100:], env_lower_slam[100:], 'b-', lw=2)
    ax2.fill_between(k_vec[100:], env_lower_slam[100:], env_upper_slam[100:], color='blue', alpha=0.25)

    # Anotaciones
    ax2.annotate('Giro 180° del Robot (Regreso al inicio)\n¡La incertidumbre odrométrica SIGUE CRECIENDO!',
                 xy=(100, true_pos[100]), xytext=(35, 120),
                 arrowprops=dict(facecolor='black', shrink=0.08, width=1.5, headwidth=8),
                 fontsize=9, fontweight='bold', bbox=dict(boxstyle='round,pad=0.4', facecolor='yellow', alpha=0.7))

    ax2.annotate('Cierre de Bucle en SLAM:\nReobserva L1 -> Colapso masivo de la trompeta',
                 xy=(105, env_upper_slam[105]), xytext=(115, 60),
                 arrowprops=dict(facecolor='blue', shrink=0.08, width=1.5, headwidth=8),
                 fontsize=9, fontweight='bold', color='blue', bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='blue'))

    ax2.set_title('2. La Trompeta de Incertidumbre ($\pm 2\sigma$): Odometría Monótona vs Colapso por Cierre de Bucle en SLAM', fontsize=12, fontweight='bold', pad=10)
    ax2.set_xlabel('Paso Temporal / Número de Comandos k', fontsize=10, fontweight='bold')
    ax2.set_ylabel('Posición / Bandas de Confianza (metros)', fontsize=10, fontweight='bold')
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='lower left', framealpha=0.9, fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path)
    print(f"Gráfica guardada exitosamente en: {output_path}")

if __name__ == "__main__":
    generate_plot()
