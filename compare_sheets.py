import pandas as pd
import requests
import io
import re

# URLs for CSV export
COMPETITOR_CSV_URL = "https://docs.google.com/spreadsheets/d/11fjg0zgjiiGdzSldx8hieID-_3crNumlQ61QR8A583M/export?format=csv"
USER_CSV_URL = "https://docs.google.com/spreadsheets/d/17S_7f8L4nYMSgJTLTxJ_DnvXdIR7YK50qKMu5NWKDvM/export?format=csv"

def normalize_text(text):
    if pd.isna(text) or text == "":
        return ""
    
    text = str(text).lower()
    
    # 1. Normalize Dates (2569 vs 2026)
    # If found 2569, replace with 2026 for comparison
    text = text.replace("2569", "2026")
    text = text.replace("พ.ศ.", "").replace("ปี", "")
    
    # 2. Remove specific Thai words that are often formatting differences
    text = text.replace("จำนวน", "").replace("รายการ", "").replace("ต้น", "")
    
    # 3. Remove all non-alphanumeric characters (including spaces, punctuation, etc.)
    # This is the most aggressive but effective way to match "สาธารณสุข 57" with "สาธารณสุข57"
    text = re.sub(r'[^\w\u0e00-\u0e7f]', '', text)
    
    return text

def compare_sheets():
    print("🚀 Downloading sheets for AI-style analysis...")
    
    try:
        # Download competitor data
        res_comp = requests.get(COMPETITOR_CSV_URL)
        df_comp = pd.read_csv(io.StringIO(res_comp.content.decode('utf-8')))
        
        # Download user data
        res_user = requests.get(USER_CSV_URL)
        df_user = pd.read_csv(io.StringIO(res_user.content.decode('utf-8')))
        
        # Column Identification
        def get_content_col(df):
            for col in df.columns:
                if 'รายการ' in str(col) or 'subject' in str(col).lower():
                    return col
            return df.columns[1]

        comp_col = get_content_col(df_comp)
        user_col = get_content_col(df_user)
        
        # Create normalized versions of the columns
        print("🧹 Normalizing data (Dates, Spaces, Units)...")
        df_comp['norm'] = df_comp[comp_col].apply(normalize_text)
        df_user['norm'] = df_user[user_col].apply(normalize_text)
        
        # Unique comparison using normalized strings
        comp_unique_norms = df_comp['norm'].unique()
        user_unique_norms = set(df_user['norm'].unique())
        
        # Find missing items
        missing_rows = []
        for norm in comp_unique_norms:
            if norm and norm not in user_unique_norms:
                # Find the original row for display
                original_row = df_comp[df_comp['norm'] == norm].iloc[0]
                missing_rows.append(original_row)
        
        df_missing = pd.DataFrame(missing_rows)
        
        print(f"\n✅ Comparison Completed.")
        print(f"📊 Competitor Unique Items: {len(comp_unique_norms)}")
        print(f"📊 Your Unique Items: {len(user_unique_norms)}")
        print(f"❌ Real Unique Missing Items: {len(df_missing)}")
        
        if len(df_missing) > 0:
            print("\n--- Top 10 Real Missing Items (Competitor has, You don't) ---")
            # Drop the 'norm' column before printing
            print(df_missing[[comp_col]].head(10).to_string(index=False))
            
            # Save to file
            df_missing.drop(columns=['norm']).to_csv("missing_items_final.csv", index=False, encoding='utf-8-sig')
            print(f"\n✅ Detailed list saved to 'missing_items_final.csv'")
            
    except Exception as e:
        print(f"❌ Error during comparison: {e}")

if __name__ == "__main__":
    compare_sheets()
