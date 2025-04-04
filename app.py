import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(layout="wide", page_title="VESC CAN Decoder")

st.title("🔧 VESC CAN Raw Data Decoder (Motorola Format)")

def decode_data(df):
    def decode_status_1(data):
        return {
            "ERPM": int.from_bytes(data[0:4], 'big', signed=True),
            "Current (A)": int.from_bytes(data[4:6], 'big', signed=True) / 10,
            "DutyCycle (%)": int.from_bytes(data[6:8], 'big', signed=True) / 10
        }

    def decode_status_2(data):
        return {
            "Amp Hours (Ah)": int.from_bytes(data[0:4], 'big', signed=True) / 1000,
            "Amp Hours Charged (Ah)": int.from_bytes(data[4:8], 'big', signed=True) / 1000
        }

    def decode_status_3(data):
        return {
            "Watt Hours (Wh)": int.from_bytes(data[0:4], 'big', signed=True) / 1000,
            "Watt Hours Charged (Wh)": int.from_bytes(data[4:8], 'big', signed=True) / 1000
        }

    def decode_status_4(data):
        return {
            "Temp FET (°C)": int.from_bytes(data[0:2], 'big', signed=True) / 10,
            "Temp Motor (°C)": int.from_bytes(data[2:4], 'big', signed=True) / 10,
            "Current In (A)": int.from_bytes(data[4:6], 'big', signed=True) / 10,
            "PID Position (°)": int.from_bytes(data[6:8], 'big', signed=True) * 0.02
        }

    def decode_status_5(data):
        return {
            "Tachometer (EREV)": int.from_bytes(data[0:4], 'big', signed=False),
            "Voltage In (V)": int.from_bytes(data[4:6], 'big', signed=False) / 10
        }

    def decode_status_6(data):
        return {
            "ADC1 (V)": int.from_bytes(data[0:2], 'big') / 1000,
            "ADC2 (V)": int.from_bytes(data[2:4], 'big') / 1000,
            "ADC3 (V)": int.from_bytes(data[4:6], 'big') / 1000,
            "PPM (%)": int.from_bytes(data[6:8], 'big') / 10
        }

    decoder = {
        0x901: decode_status_1,
        0xE01: decode_status_2,
        0xF01: decode_status_3,
        0x1001: decode_status_4,
        0x1B01: decode_status_5,
        0x1C01: decode_status_6,
    }

    decoded = []
    for _, row in df.iterrows():
        can_id = row['can_id']
        if can_id in decoder:
            data_bytes = bytes([row[f'byte{i}'] for i in range(1, 9)])
            result = decoder[can_id](data_bytes)
            result['CAN_ID'] = hex(can_id)
            result['Timestamp'] = row['timestamp']
            decoded.append(result)

    return pd.DataFrame(decoded)


uploaded_file = st.file_uploader("Upload your raw CAN CSV file", type=["csv"])

if uploaded_file:
    df_raw = pd.read_csv(uploaded_file)
    decoded_df = decode_data(df_raw)

    st.success("✅ Data decoded successfully!")
    st.dataframe(decoded_df, use_container_width=True)

    # Plot (if data exists)
    if 'ERPM' in decoded_df.columns:
        st.line_chart(decoded_df[['Timestamp', 'ERPM']].dropna().set_index('Timestamp'))

    if 'Voltage In (V)' in decoded_df.columns:
        st.line_chart(decoded_df[['Timestamp', 'Voltage In (V)']].dropna().set_index('Timestamp'))

    # Download link
    csv = decoded_df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇ Download Processed CSV", data=csv, file_name="decoded_data.csv", mime='text/csv')
