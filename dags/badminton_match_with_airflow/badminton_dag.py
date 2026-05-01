import sys
import os

current_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, current_dir)

import config_dag as cd
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import pandas as pd

def extract_transform_load():
    TARGET_HARI = 30
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'X-Fsign': cd.xfsign_code
    }
    
    today = datetime.now().date()
    
    # Looping dari 0 (hari ini) mundur sampai TARGET_HARI-1 hari yang lalu
    for i in range(TARGET_HARI):
        offset = -i 
        target_date = today + timedelta(days=offset)
        tanggal_str = target_date.strftime('%Y-%m-%d')
        
        print(f"[{tanggal_str}] Mulai nyedot data dengan offset {offset}...")
        
        url = cd.url.format(offset)
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"Gagal narik tanggal {tanggal_str}. Code: {response.status_code}")
            continue # Lanjut ke hari berikutnya kalau gagal
            
        raw_text = response.text
        records = raw_text.split('~')
        
        parsed_data = []
        for record in records:
            if not record: continue
            row_dict = {}
            fields = record.split('¬')
            for field in fields:
                if '÷' in field:
                    key, value = field.split('÷', 1)
                    row_dict[key] = value
            parsed_data.append(row_dict)
            
        df = pd.DataFrame(parsed_data)
        
        if 'AA' not in df.columns:
            print(f"[{tanggal_str}] ZONK! GOR RW sepi bos, ga ada event BWF sama sekali. Skip!")
            continue # Langsung putar loop ke hari selanjutnya
            
        df_matches = df[df['AA'].notna()].copy()
        
        # CEK JUMLAH BARIS DATAFRAME
        if len(df_matches) == 0:
            print(f"[{tanggal_str}] ZONK! Dataframe kopong. Skip!")
            continue # Langsung putar loop ke hari selanjutnya
            
        # Tiap iterasi loop, save ke CSV dengan nama tanggal masing-masing
        destination_path = f'/opt/airflow/dags/output-badminton-match-with-airflow/hasil_badminton_{tanggal_str}.csv'
        df_matches.to_csv(destination_path, index=False)
        print(f"[{tanggal_str}] Sukses disave! ({len(df_matches)} baris)")

# Konfigurasi default Airflow
default_args = {
    'owner': 'abilhzn',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Definisi DAG
with DAG(
    dag_id='badminton_flashscore',
    default_args=default_args,
    start_date=datetime(2026, 4, 30),
    schedule_interval='@daily', # Jalan tiap hari
    catchup=False
) as dag:

    # Task tunggal kita
    etl_task = PythonOperator(
        task_id='tarik_dan_bersihkan_data',
        python_callable=extract_transform_load
    )

    # Kalau ada banyak task, di sini tempat ngatur panahnya (misal: task1 >> task2)
    etl_task