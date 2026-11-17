import numpy as np
import matplotlib.pyplot as plt

# Original signal x(t)
def x(t):
    y = np.zeros_like(t)

    # -1 <= t < 0 : ramp
    mask = (t >= -1) & (t < 0)
    y[mask] = t[mask] + 1

    # 0 <= t < 1 : level 2
    mask = (t >= 0) & (t < 1)
    y[mask] = 2

    # 1 <= t < 2 : level 1
    mask = (t >= 1) & (t < 2)
    y[mask] = 1

    return y

# Time axis
t = np.linspace(-5, 5, 4000)

# Transformed signals
y1 = x(t - 2)          # x(t-2)
y2 = x(2*t + 3)        # x(2t+3)
y3 = x(1.5*t)          # x(3t/2)
y4 = x(-t + 1)         # x(-t+1)

titles = [
    r'$x(t-2)$',
    r'$x(2t+3)$',
    r'$x\left(\frac{3}{2}t\right)$',
    r'$x(-t+1)$'
]

signals = [y1, y2, y3, y4]

fig, axs = plt.subplots(2, 2, figsize=(12,8))

for ax, y, title in zip(axs.ravel(), signals, titles):
    ax.plot(t, y, linewidth=2)
    ax.set_title(title)
    ax.set_xlabel('t')
    ax.set_ylabel('Amplitude')
    ax.grid(True)
    ax.axhline(0, color='black', linewidth=1)
    ax.axvline(0, color='black', linewidth=1)
    ax.set_xlim(-5,5)
    ax.set_ylim(-0.5,2.5)

plt.tight_layout()
plt.show()