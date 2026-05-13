import pandas as pd
import matplotlib.pyplot as plt

# Define the file path
file_path = '/home/christopher/sciebo/SoSe2026/HPC Lab/Analyse/Lab 5/assignment2-2.csv'

# Mapping for the x-values (Vector Length in bits)
config_mapping = {
    'config_0': 128,
    'config_1': 256,
    'config_2': 512,
    'config_3': 1024
}

def plot_simd_efficiency(csv_path):
    # Load the dataset
    df = pd.read_csv(csv_path)

    # Column aliases for readability based on gem5 output names
    total_col = 'board.processor.cores.core.commit.committedInstType_0::total'
    cmp_col = 'board.processor.cores.core.commit.committedInstType_0::SimdCmp'
    fma_col = 'board.processor.cores.core.commit.committedInstType_0::SimdFloatMultAcc'

    # 1. Parse the run_name to extract configuration and benchmark type
    # run_name format: config_N-benchmark-type
    df[['config', 'benchmark', 'type']] = df['run_name'].str.split('-', expand=True)
    df['label'] = df['benchmark'] + '-' + df['type']
    df['x_val'] = df['config'].map(config_mapping)

    # 2. Calculate instruction counts
    # SIMD instructions is the sum of SimdCmp and SimdFloatMultAcc
    df['simd_insts'] = df[cmp_col] + df[fma_col]
    # Scalar instructions is Total - SIMD
    df['scalar_insts'] = df[total_col] - df['simd_insts']

    # 3. Calculate SIMD efficiency using the provided formula:
    # ((scalar instructions / simd instructions) / x-value)
    df['efficiency'] = (df['scalar_insts'] / df['simd_insts']) / df['x_val']

    # 4. Plotting
    plt.figure(figsize=(10, 6))
    
    # Get unique labels (daxpy-acle, daxpy-sve, simple_triad-acle, simple_triad-sve)
    labels = df['label'].unique()
    
    for label in labels:
        subset = df[df['label'] == label].sort_values('x_val')
        plt.plot(subset['x_val'], subset['efficiency'], marker='o', label=label)

    plt.xlabel('Vector Length (bits)')
    plt.ylabel('SIMD Efficiency')
    plt.title('SIMD Efficiency of daxpy and simple_triad (sve, acle) vs Vector Length')
    plt.xticks([128, 256, 512, 1024])
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    # Show the plot
    plt.tight_layout()
    # plt.show()
    plt.savefig("simd-efficiency.png")

if __name__ == "__main__":
    try:
        plot_simd_efficiency(file_path)
    except Exception as e:
        print(f"Error processing CSV: {e}")
