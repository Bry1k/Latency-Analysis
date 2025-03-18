import os
import sys
import re
import statistics

def parse_latency_data(report_file):
    """ Parses the DPC/ISR latency data from the XPerf report """
    latencies = []
    driver_latencies = {}
    core_latencies = {}

    with open(report_file, "r") as file:
        lines = file.readlines()

    for line in lines:
        # Extract latency histogram data
        match = re.search(r"Elapsed Time, >\s*(\d+) usecs AND <=\s*(\d+) usecs,\s*(\d+),", line)
        if match:
            lower_bound, upper_bound, count = map(int, match.groups())
            avg_latency = (lower_bound + upper_bound) / 2
            latencies.extend([avg_latency] * count)

        # Extract driver latency contributions
        driver_match = re.search(r"Total = (\d+) for module (\S+)", line)
        if driver_match:
            count, driver = driver_match.groups()
            driver_latencies[driver] = driver_latencies.get(driver, 0) + int(count)

        # Extract per-core latencies
        core_match = re.findall(r"CPU (\d+) Usage,.*?(\d+)\s+usec,", line)
        if core_match:
            for core, latency in core_match:
                core_latencies[core] = core_latencies.get(core, 0) + int(latency)

    return latencies, driver_latencies, core_latencies

def display_results(latencies, driver_latencies, core_latencies, output_file):
    """ Calculates and displays various latency statistics """
    with open(output_file, "w") as file:
        if not latencies:
            file.write("\n===== LATENCY RESULTS =====\n")
            file.write("No latency data found.\n")
            return

        highest_latency = max(latencies)
        avg_latency = sum(latencies) / len(latencies)
        median_latency = statistics.median(latencies)
        percentile_90 = statistics.quantiles(latencies, n=10)[8]  # 90th percentile
        percentile_95 = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
        percentile_99 = statistics.quantiles(latencies, n=100)[98]  # 99th percentile
        percentile_999 = statistics.quantiles(latencies, n=1000)[998]  # 99.9th percentile
        stddev_latency = statistics.stdev(latencies)

        file.write("\n===== LATENCY RESULTS =====\n")
        file.write(f"Highest measured interrupt to process latency: {highest_latency:.2f} µs\n")
        file.write(f"Average measured interrupt to process latency: {avg_latency:.2f} µs\n")
        file.write("\n")
        file.write(f"Median interrupt to process latency: {median_latency:.2f} µs\n")
        file.write(f"90th Percentile interrupt to process latency: {percentile_90:.2f} µs\n")
        file.write(f"95th Percentile interrupt to process latency: {percentile_95:.2f} µs\n")
        file.write(f"99th Percentile interrupt to process latency: {percentile_99:.2f} µs\n")
        file.write(f"99.9th Percentile interrupt to process latency: {percentile_999:.2f} µs\n")
        file.write(f"Standard Deviation: {stddev_latency:.2f} µs\n\n")

        file.write("===== DRIVER LATENCY CONTRIBUTION =====\n")
        if driver_latencies:
            sorted_drivers = sorted(driver_latencies.items(), key=lambda x: x[1], reverse=True)
            for driver, count in sorted_drivers[:10]:  # Show top 10 drivers
                file.write(f"{driver}: {count} occurrences\n")
        else:
            file.write("No driver latency data found.\n")

def main():
    if len(sys.argv) < 3:
        print("Usage: python analyze.py <report_file> <output_file>")
        sys.exit(1)

    report_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if not os.path.exists(report_file):
        print(f"Error: Report file '{report_file}' not found.")
        sys.exit(1)

    print(f"[+] Analyzing: {report_file}")

    latencies, driver_latencies, core_latencies = parse_latency_data(report_file)
    display_results(latencies, driver_latencies, core_latencies, output_file)

if __name__ == "__main__":
    main()