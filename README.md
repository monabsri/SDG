# Synthetic Data Generation for Gear Defect Detection
This repository provides the data used for a gear defect detection model. It contains 
10,000 synthetic images generated using a simulation-based pipeline and two real-world datasets (T1 and T2) for hybrid training and 
evaluation. 
The dataset includes images and labels for three classes: ok, rust, and defect.

## Dataset
Dataset structure: 

• /synthetic_images/: 10000 synthetic images and .txt labels generated via NVIDIA 
Isaac Sim 

• /real_word_T1/: First real-world gear images and their corresponding labels used for 
evaluation and hybrid training strategy 

• /real_world_T2/: Second real-world gear images and their corresponding labels used 
for further evaluation

## Classes
- ok: intact gear
- rust: surface corrosion
- defect: geometry-based damage

## Scripts
The repository includes a Python script for dataset generation, including scene setup, domain randomization, and automatic label generation.

## Usage
The dataset can be used for training object detection models such as YOLO.
Annotations are provided in YOLO format.

## License
This project is licensed under the MIT License – see the LICENSE file for details.
The code references NVIDIA MDL materials available within Isaac Sim installations. 
No NVIDIA assets or material files are redistributed in this repository.
