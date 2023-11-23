from mm_pymu_pdf import PyMuPDFReader

loader = PyMuPDFReader()
documents = loader.load_data(file_path="./data/design.pdf", metadata=True)


print(len(documents))
