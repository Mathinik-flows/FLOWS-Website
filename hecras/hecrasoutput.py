import h5py
import pandas as pd

def explore_hdf5(group, indent=0):
    #recursively explore HDF5 Structure
    for key in group.keys():
        item = group[key]
        if isinstance(item, h5py.Group):
            print("    " * indent  + f"[Group] {key}")
            explore_hdf5(item, indent + 1)
        else:
            print("    " * indent + f"[Dataset] {key} -> shape: {item.shape}, dtype: {item.dtype}")

def list_groups(hdf5_group):
    groups = [key for key in hdf5_group.keys() if isinstance(hdf5_group[key], h5py.Group)]
    print("Groups: ", groups)

def list_datasets(hdf5_group):
    datasets = [key for key in hdf5_group.keys() if isinstance(hdf5_group[key], h5py.Dataset)]
    print("Datasets: ", datasets)

with h5py.File("flow.p09.hdf", "r") as f:
    # print("HDF5 File Structure: ")
    
    #explore_hdf5(f)

    # group = f["Results"]["Unsteady"]["Output"]["Output Blocks"]["Base Output"]["Unsteady Time Series"]["2D Flow Areas"]["river"]
    # list_groups(group)
    # list_datasets(group)

    # dataset_path = "Results/Unsteady/Output/Output Blocks/Base Output/Unsteady Time Series/2D Flow Areas/river/Water Surface" 
    # dataset = f[dataset_path]
    # data = dataset[:]
    # # print(f"Extracted data from {dataset_path}")
    # # print(data)
    # # print(dataset.shape[0])


    # df = pd.DataFrame(data)

    # excel_file_path = r"C:\Yna\Thesis\FLOWS\hecras\elevation_data.csv"
    # df.to_csv(excel_file_path, index=False, header=False)


    # group = f["Geometry"]["2D Flow Areas"]["river"]
    # list_groups(group)
    # list_datasets(group)

    # dataset_path = "Geometry/2D Flow Areas/river/FacePoints Coordinate" 
    # dataset = f[dataset_path]
    # data = dataset[:]

    # df = pd.DataFrame(data)

    # excel_file_path = r"C:\Yna\Thesis\FLOWS\hecras\fcoordinates_data.csv"
    # df.to_csv(excel_file_path, index=False, header=False)

    group = f["Geometry"]["2D Flow Areas"]["river"]
    list_groups(group)
    list_datasets(group)

    dataset_path = "Geometry/2D Flow Areas/river/Cells Face and Orientation Info" 
    dataset = f[dataset_path]
    data = dataset[:]

    df = pd.DataFrame(data)

    excel_file_path = r"C:\Yna\Thesis\FLOWS\hecras\cficoordinates_data.csv"
    df.to_csv(excel_file_path, index=False, header=False)