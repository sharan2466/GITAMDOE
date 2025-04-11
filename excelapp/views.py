import os
import pandas as pd
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponseRedirect

def home(request):
    return render(request, 'excelapp/home.html')

def compare_excel(request):
    context = {}
    if request.method == 'POST':
        file1 = request.FILES.get('file1')
        file2 = request.FILES.get('file2')
        mapping_input = request.POST.get('mappings')

        fs = FileSystemStorage()
        path1 = fs.save(file1.name, file1)
        path2 = fs.save(file2.name, file2)
        full_path1 = fs.path(path1)
        full_path2 = fs.path(path2)

        try:
            df1 = pd.read_excel(full_path1)
            df2 = pd.read_excel(full_path2)

            # Parse mapping input like: [Registration number]=REGDNO
            mappings = {}
            for item in mapping_input.split(","):
                left, right = item.strip().split("=")
                left = left.strip().strip("[](){}")
                right = right.strip().strip("[](){}")
                if left not in df1.columns:
                    raise ValueError(f"'{left}' not in File1 columns")
                if right not in df2.columns:
                    raise ValueError(f"'{right}' not in File2 columns")
                mappings[left] = right

            # Subset and align columns based on mapping
            df1_subset = df1[list(mappings.keys())].copy()
            df2_subset = df2[list(mappings.values())].copy()
            df2_subset.columns = list(mappings.keys())  # Rename for matching

            # Perform outer merge to find differences
            merged_df = df1_subset.merge(df2_subset, on=list(mappings.keys()), how='outer', indicator=True)

            # Not found in File2 (Manual registrations not matched in preprocess data)
            not_found_in_file2 = merged_df[merged_df['_merge'] == 'left_only'].drop(columns=['_merge'])
            not_found_in_file2 = not_found_in_file2.merge(df1, how='left', on=list(mappings.keys()))
            not_found_in_file2['Remarks'] = f"{file2.name}_Not_Found"

            # Not found in File1 (Preprocess data not matched in manual registrations)
            not_found_in_file1 = merged_df[merged_df['_merge'] == 'right_only'].drop(columns=['_merge'])
            not_found_in_file1 = not_found_in_file1.merge(df2, how='left', left_on=list(mappings.keys()), right_on=list(mappings.values()))
            not_found_in_file1['Remarks'] = f"{file1.name}_Not_Found"

            # Generate output filenames
            output1_name = f"Not_Found_{os.path.splitext(file2.name)[0]}.xlsx"
            output2_name = f"Not_Found_{os.path.splitext(file1.name)[0]}.xlsx"

            # Save outputs to media folder
            output_path1 = os.path.join('media', output1_name)
            output_path2 = os.path.join('media', output2_name)
            not_found_in_file2.to_excel(output_path1, index=False)
            not_found_in_file1.to_excel(output_path2, index=False)

            # Provide download links
            context['download1'] = f"/media/{output1_name}"
            context['download2'] = f"/media/{output2_name}"

        except Exception as e:
            context['error'] = str(e)

    return render(request, 'excelapp/compare_excel.html', context)
