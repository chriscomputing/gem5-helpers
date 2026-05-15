import pandas as pd
import matplotlib.pyplot as plt

# Define the file path
file_path = '/home/christopher/sciebo/SoSe2026/HPC Lab/Analyse/Lab 5/tables/lab5_assignment4-2_all.csv'

# Mapping for the x-values (Vector Length in bits)
config_mapping = {
    'config_0': 128,
    'config_1': 256,
    'config_2': 512,
    'config_3': 1024,
    "config_4": 2048
}

def plot_simd_efficiency(csv_path):
    # Load the dataset
    df = pd.read_csv(csv_path)

    # Column aliases for readability based on gem5 output names
    ipc = "board.processor.cores.core.ipc"
    cycles = "board.processor.cores.core.numCycles"
    print(df.head())

    # 1. Parse the run_name to extract configuration and benchmark type
    # run_name format: config_N-benchmark-type
    df[['config', 'benchmark', 'type']] = df['run_name'].str.split('-', expand=True)
    df['label'] = df['benchmark'] + '-' + df['type']
    df['x_val'] = df['config'].map(config_mapping)

    # 4. Plotting
    plt.figure(figsize=(10, 6))
    
    # Get unique labels (daxpy-acle, daxpy-sve, simple_triad-acle, simple_triad-sve)
    labels = df['label'].unique()
    
    for label in labels:
        subset = df[df['label'] == label].sort_values('x_val')
        plt.plot(subset['x_val'], subset[cycles], marker='o', label=label)

    plt.xlabel('Vector Length (bits)')
    plt.ylabel('SIMD Efficiency')
    plt.title('SIMD Efficiency vs Vector Length (spmv)')
    plt.xticks([128, 256, 512, 1024, 2048])
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    # Show the plot
    plt.tight_layout()
    # plt.show()
    plt.savefig("assignment4-2_all_cycles.png")

if __name__ == "__main__":
    try:
        plot_simd_efficiency(file_path)
    except Exception as e:
        print(f"Error processing CSV: {e}")
