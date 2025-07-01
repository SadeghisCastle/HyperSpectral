import csv
from nptdms import TdmsFile

def tdms_to_csv(tdms_path, csv_path):
    tdms_file = TdmsFile.read(tdms_path)
    all_data = {}
    channel_names = []

    # Read all channels across all groups
    for group in tdms_file.groups():
        for channel in group.channels():
            full_name = f"{group.name}/{channel.name}"
            channel_names.append(full_name)
            all_data[full_name] = channel[:]

    # Find the maximum number of samples
    num_rows = max(len(data) for data in all_data.values())

    # Write to CSV
    with open(csv_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(channel_names)  # header

        for i in range(num_rows):
            row = [all_data[name][i] if i < len(all_data[name]) else "" for name in channel_names]
            writer.writerow(row)

    print(f"Saved to {csv_path}")

# Example usage
tdms_to_csv(".venv/Instrument Capture 2025-06-12 15-04-35.tdms", "output.csv")
