import pandas as pd
import os

# create outputs directory if it doesn't exist
os.makedirs('outputs', exist_ok=True)

# load the data
approvals = pd.read_csv('approvals_00OUf000004eCTBMA2.csv')
requests = pd.read_csv('requests_00OUf000005GbLiMAK.csv', encoding='latin-1')

# convert date columns to datetime
approvals['Step Completed Date'] = pd.to_datetime(approvals['Step Completed Date'])

# filter for only po approval and president approval steps
po_approvals = approvals[approvals['Step: Name'] == 'PO Approval'][['Record Name', 'Step Completed Date']].copy()
po_approvals.columns = ['Record Name', 'PO Approval Date']

president_approvals = approvals[approvals['Step: Name'] == 'President Approval'][['Record Name', 'Step Completed Date']].copy()
president_approvals.columns = ['Record Name', 'President Approval Date']

# merge the two approval steps
approval_times = po_approvals.merge(president_approvals, on='Record Name', how='inner')

# calculate days between approvals
approval_times['Days'] = (approval_times['President Approval Date'] - approval_times['PO Approval Date']).dt.days

# calculate business days (excluding weekends)
def count_business_days(start_date, end_date):
    business_days = 0
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() < 5:  # monday=0, sunday=6
            business_days += 1
        current_date += pd.Timedelta(days=1)
    return business_days

approval_times['Business Days'] = approval_times.apply(
    lambda row: count_business_days(row['PO Approval Date'], row['President Approval Date']),
    axis=1
)

# extract year from president approval date
approval_times['Year'] = approval_times['President Approval Date'].dt.year

# merge with requests to get program information
approval_times_with_program = approval_times.merge(
    requests[['Request: Reference Number', 'Top Level Primary Program']],
    left_on='Record Name',
    right_on='Request: Reference Number',
    how='left'
)

# calculate average days by year and program
year_program_avg = approval_times_with_program.groupby(['Year', 'Top Level Primary Program']).agg({
    'Days': 'mean',
    'Business Days': 'mean'
}).round(2)

print("\naverage days from po approval to president approval by year and program:")
print(year_program_avg)

# save to csv
year_program_avg_df = year_program_avg.reset_index()
year_program_avg_df.columns = ['Year', 'Program', 'Approval Time (Average)', 'Approval Time Excl. Weekends (Average)']
year_program_avg_df = year_program_avg_df.sort_values(['Year', 'Program'])
year_program_avg_df.to_csv('outputs/approval_days_by_program.csv', index=False)

print(f"\nresults saved to outputs/approval_days_by_program.csv")
print(f"\ntotal records: {len(year_program_avg_df)}")
print(f"years covered: {sorted(year_program_avg_df['Year'].unique())}")