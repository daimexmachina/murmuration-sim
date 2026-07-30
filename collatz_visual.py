import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def collatz_sequence(n, max_steps=10000):
    seq = [n]
    while n != 1 and len(seq) < max_steps:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        seq.append(n)
    return seq

def main():
    # Starting values for trajectories
    seeds = [7, 27, 97, 873]
    
    # Setup figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('The Collatz Conjecture (3n + 1 Problem)', fontsize=16, fontweight='bold')

    # Panel 1: Trajectories
    colors = plt.cm.tab10(np.linspace(0, 1, len(seeds)))
    for i, seed in enumerate(seeds):
        seq = collatz_sequence(seed)
        ax1.plot(seq, color=colors[i], label=f'n={seed}', linewidth=2, marker='o', markersize=3, alpha=0.8)
    
    ax1.set_yscale('log')
    ax1.set_title('Trajectories of Selected Seeds', fontsize=13)
    ax1.set_xlabel('Step')
    ax1.set_ylabel('Value (Log Scale)')
    ax1.grid(True, which="both", ls="-", alpha=0.2)
    ax1.axhline(1, color='black', linewidth=1, linestyle='--', label='Target (1)')
    ax1.legend()

    # Panel 2: Stopping Times
    n_range = range(1, 101)
    stopping_times = [len(collatz_sequence(n)) - 1 for n in n_range]
    
    ax2.bar(n_range, stopping_times, color='skyblue', edgecolor='navy', alpha=0.7)
    ax2.set_title('Stopping Times (n=1 to 100)', fontsize=13)
    ax2.set_xlabel('Starting Integer (n)')
    ax2.set_ylabel('Steps to reach 1')
    ax2.grid(axis='y', ls='--', alpha=0.5)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    output_path = 'collatz_visualization.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Visualization saved to {output_path}")

if __name__ == "__main__":
    main()
