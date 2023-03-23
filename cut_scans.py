import os
import sys
import cv2
import numpy
from pdf2image import convert_from_path
from pikepdf import Pdf
from pyzbar.pyzbar import decode, ZBarSymbol

# check if there are 2 arguments
if len(sys.argv) != 3:
    print("Użycie: python cut_scans.py [input_dir|input_file] output_path")
    sys.exit(1)

# read arguments
input_path, output_path = sys.argv[1:]

# check if output path exists and is a directory
if not os.path.isdir(output_path):
    print("Output path is not a directory")
    sys.exit(1)

# create folders from zadanie 1 to zadanie 6 in input path if they don't exist
for i in range(1, 7):
    zadanie_path = os.path.join(output_path, "zadanie" + str(i))
    if not os.path.exists(zadanie_path):
        os.makedirs(zadanie_path)
        print("Stworzono folder " + zadanie_path)

# generate list of input files.
input_files = None
if not os.path.isdir(input_path):
    # check if input path is a file
    if not os.path.isfile(input_path):
        print("Input path is not a file or directory")
        sys.exit(1)
    input_files = [input_path]
else:
    input_multiple_file = True
    input_files = list(os.listdir(input_path))
    # add input path to file names
    input_files = [os.path.join(input_path, f) for f in input_files]

# iterate over files in input path and extract pdfs from them
for file_name in input_files:
    # check if file is a pdf
    if not file_name.endswith(".pdf"):
        print("Pominięto plik " + file_name + " bo nie jest to plik pdf.")
        continue
    
    print("Przetwarzam plik " + file_name)

    pages = convert_from_path(file_name, thread_count=100)
    split = {}
    filenames = {}
    
    cur_filename = None
    first_page_id = None
    page_id = 0
    for page in pages:
        img = cv2.cvtColor(numpy.array(page), cv2.COLOR_RGB2BGR)
        value = decode(img, symbols=[ZBarSymbol.QRCODE]).pop().data.decode("ascii", errors="ignore")
        
        if cur_filename is None and value is None:
            print("ERROR: Nie znaleziono kodu QR na pierwszej stronie")
        
        if len(value) > 0:
            if cur_filename is not None:
                # save previous file as pdf
                split[len(split)] = [first_page_id, page_id]
                filenames[len(filenames)] = cur_filename
                print(f"Wyodrębiono plik {cur_filename}.")
            cur_filename = value
            first_page_id = page_id
        page_id += 1

    split[len(split)] = [first_page_id, page_id]
    filenames[len(filenames)] = cur_filename
    print(f"Wyodrębiono plik {cur_filename}.")
    
    pdf = Pdf.open(file_name)

    # make the new splitted PDF files
    new_pdf_files = [Pdf.new() for i in split]
    # the current pdf file index
    new_pdf_index = 0
    
    for n, page in enumerate(pdf.pages):
        if new_pdf_index not in split:
            break
        if n in list(range(*split[new_pdf_index])):
            # add the `n` page to the `new_pdf_index` file
            new_pdf_files[new_pdf_index].pages.append(page)
        else:
            # make a unique filename based on original file name plus the index
            name = filenames[new_pdf_index]
            problem_name = name.split("-", 1)[1].split("&")[0]
            filename = name.split("-", 1)[1].split("&")[1] + "-" + name.split("-", 1)[0]
            output_filename = f"{filename}.pdf"
            # save the PDF file
            new_pdf_files[new_pdf_index].save(os.path.join(output_path, "zadanie" + problem_name, output_filename))
            print(f"Zapisano plik {output_filename}.")
            # go to the next file
            new_pdf_index += 1
            # add the `n` page to the `new_pdf_index` file
            if len(new_pdf_files) <= new_pdf_index:
                break
            new_pdf_files[new_pdf_index].pages.append(page)
            
    if new_pdf_index in split:
        name = filenames[new_pdf_index]
        problem_name = name.split("-", 1)[1].split("&")[0]
        filename = name.split("-", 1)[1].split("&")[1] + "-" + name.split("-", 1)[0]
        output_filename = f"{filename}.pdf"
        # save the PDF file
        new_pdf_files[new_pdf_index].save(os.path.join(output_path, "zadanie" + problem_name, output_filename))
        print(f"Zapisano plik {output_filename}.")
    


# print report
print("Raport:")
for i in range(1, 7):
    zadanie_path = os.path.join(output_path, "zadanie" + str(i))
    # how much pdf files are in folder
    files = [f for f in os.listdir(zadanie_path) if os.path.isfile(os.path.join(zadanie_path, f))]
    # remove non pdf
    files = [f for f in files if f.endswith(".pdf")]
    print(f"W folderze zadanie{i} jest {len(files)} plików pdf.")
    