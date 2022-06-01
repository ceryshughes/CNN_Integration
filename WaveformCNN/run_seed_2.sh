#!/bin/bash
#SBATCH -c 4  # Number of Cores per Task
#SBATCH --mem=8192  # Requested Memory
#SBATCH -p gpu  # Partition
#SBATCH -G 1  # Number of GPUs
#SBATCH -t 24:00:00  # Job time limit
#SBATCH -o slurm-%j.out  # %j = job ID
 
module load cuda/10
/modules/apps/cuda/10.1.243/samples/bin/x86_64/linux/release/deviceQuery

#Make sure to run 'conda init bash' before running this script!

module load miniconda/4.11.0
#conda init bash
#conda activate cerys

#pip3 install tensorflow==2.6
#pip3 install keras==2.6
#pip3 install librosa==0.8.1

#python3.8 train_cnn.py
seed_num=2
conda run -n fresh --no-capture-output python3.8 train_cnn.py $seed_num saved_models/run_seed_$seed_num ../klatt_synthesis/sounds_pulse_voicing_artificial_closure_dur/ laff_vcv/sampled_stop_categories_pulse_voicing_artificial_closure_dur.csv > run_seed_${seed_num}_out.txt 

