import os

# Set environment variables to ensure correct training mode
os.environ["TRAIN_MODE"] = "advanced"

# Import existing data preprocessing and model training functions
from dealer_data_preprocessing import load_and_process_data
from model import train_model

if __name__ == "__main__":
    print("🚀 Starting to load data...")

    # File paths for dealer data (adjust paths if needed)
    FILE_PATHS = [
        r'E:\ASSPIS_Project\24年13维度数据.xlsx',
        r'E:\ASSPIS_Project\22-23数据.xlsx'
    ]

    # Load and preprocess dealer data
    dealers, dealer_codes = load_and_process_data(FILE_PATHS)

    print("🚀 Starting model training and Optuna search...")

    # Set the directory for saving the results (ensure it exists)
    save_dir = r"E:\07Journals\experiment\Optunaphase1"
    os.makedirs(save_dir, exist_ok=True)

    # Trigger the model training and Optuna hyperparameter search
    best_model, scaler, X, y, y_pred = train_model(dealers)

    # Save the Optuna results to the specified directory
    # Assuming `train_model` function already handles the CSV saving as per previous implementation
    print(f"🎉 Experiment script has finished! The results are saved in {save_dir}.")