#!/bin/bash
#SBATCH -c 4  # Number of Cores per Task
#SBATCH --mem=8192  # Requested Memory
#SBATCH -p gpu  # Partition
#SBATCH -G 1  # Number of GPUs
#SBATCH -t 24:00:00  # Job time limit
#SBATCH -o slurm-%j.out  # %j = job ID
 
module load cuda/10
/modules/apps/cuda/10.1.243/samples/bin/x86_64/linux/release/deviceQuery

module load python/3.8
pip install tensorflow==2.6
pip install keras==2.6
pip install librosa==0.8.1

python3.8 train_cnn.py