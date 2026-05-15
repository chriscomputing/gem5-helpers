import pandas as pd
import matplotlib.pyplot as plt
import os
import traceback

# Define the file path
file_path = '/home/christopher/sciebo/SoSe2026/HPC Lab/Analyse/Lab 5/tables/lab5_assignment4-1_matmult-bt.csv'

# Mapping for the x-values (Vector Length in bits)
config_mapping = {
    'config_0': 128,
    'config_1': 256,
    'config_2': 512,
    'config_3': 1024,
    "config_4": 2048
}

def plot_simd_efficiency(csv_path):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at: {csv_path}")

    # Load the dataset
    df = pd.read_csv(csv_path)

# Column aliases for readability based on gem5 output names
    # Scalar instructions
    sAlu = "board.processor.cores.core.commit.committedInstType_0::IntAlu"
    sMult = "board.processor.cores.core.commit.committedInstType_0::IntMult"
    sDiv = "board.processor.cores.core.commit.committedInstType_0::IntDiv"
    sFlAdd = "board.processor.cores.core.commit.committedInstType_0::FloatAdd"
    sFlCm = "board.processor.cores.core.commit.committedInstType_0::FloatCmp"
    sFlCv = "board.processor.cores.core.commit.committedInstType_0::FloatCvt"
    all_scalar = "scalars"

    # Vector instructions
    vAdd = "board.processor.cores.core.commit.committedInstType_0::SimdAdd"
    vAlu = "board.processor.cores.core.commit.committedInstType_0::SimdAlu"
    vCmp = "board.processor.cores.core.commit.committedInstType_0::SimdCmp"
    vPAl = "board.processor.cores.core.commit.committedInstType_0::SimdPredAlu"
    vFlMult = "board.processor.cores.core.commit.committedInstType_0::SimdFloatMultAcc"
    vFlRdA = "board.processor.cores.core.commit.committedInstType_0::SimdFloatReduceAdd"
    all_vectors = "vectors"

    # Validation: Ensure all required columns exist
    required_columns = [
        'run_name', sAlu, sMult, sDiv, sFlAdd, sFlCm, sFlCv,
        vAdd, vAlu, vCmp, vPAl, vFlMult, vFlRdA
    ]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise KeyError(f"The following required columns are missing from the CSV: {missing}")

    # 1. Parse the run_name to extract configuration and benchmark type
    # Use n=2 to limit the split to 3 parts (config, benchmark, the rest).
    # This prevents crashes if benchmark names or suffixes contain extra hyphens.
    split_df = df['run_name'].str.split('-', n=2, expand=True)

    # Handle cases where run_name might have fewer than 2 hyphens (e.g. 'config_0-spmv')
    # We pad the dataframe with 'default' values to ensure we always have 3 columns.
    for i in range(split_df.shape[1], 3):
        split_df[i] = "default"

    df[['config', 'benchmark', 'type']] = split_df[[0, 1, 2]]

    df['label'] = df['benchmark'] + '-' + df['type']
    
    # Validation: Mapping check
    df['x_val'] = df['config'].map(config_mapping)
    if df['x_val'].isnull().any():
        unmapped = df[df['x_val'].isnull()]['config'].unique()
        raise ValueError(f"The following configurations were not found in config_mapping: {unmapped}")

    # Math where needed
    df[all_scalar] = df[sAlu]+df[sMult]+df[sDiv]+df[sFlAdd]+df[sFlCm]+df[sFlCv]
    df[all_vectors] = df[vAdd]+df[vAlu]+df[vCmp]+df[vPAl]+df[vFlMult]+df[vFlRdA]

    # Calculate SIMD efficiency as ((all_scalar/all_vectors)/vector length in bits)
    eff = "eff"
    df[eff] = (df[all_scalar] / df[all_vectors]) / df['x_val']

    # 4. Plotting
    plt.figure(figsize=(10, 6))
    
    # Get unique labels (daxpy-acle, daxpy-sve, simple_triad-acle, simple_triad-sve)
    labels = df['label'].unique()
    
    for label in labels:
        subset = df[df['label'] == label].sort_values('x_val')
        plt.plot(subset['x_val'], subset[eff], marker='o', label=label)

    plt.xlabel('Vector Length (bits)')
    plt.ylabel('SIMD Efficiency')
    plt.title('SIMD Efficiency of bt matmult vs Vector Length')
    plt.xticks([128, 256, 512, 1024, 2048])
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    # Show the plot
    plt.tight_layout()
    # plt.show()
    plt.savefig("assignment4-1_matmult-bt.png")

if __name__ == "__main__":
    try:
        plot_simd_efficiency(file_path)
    except Exception as e:
        print(f"Error processing CSV: {e}\n{traceback.format_exc()}")
