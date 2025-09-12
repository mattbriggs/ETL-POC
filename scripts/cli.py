
#!/usr/bin/env python3
import argparse
from dita_etl import build_flow

def main():
    p = argparse.ArgumentParser(description="Run DITA ETL pipeline (Prefect flow).")
    p.add_argument("--config", default="config/config.yaml")
    p.add_argument("--input", default="sample_data/input")
    args = p.parse_args()
    result = build_flow(config_path=args.config, input_dir=args.input)
    print(f"Pipeline completed. Map at: {result}")

if __name__ == "__main__":
    main()
