import os


def convert(indir, outdir):
    outdir_new = os.path.join(outdir, 'djvu2txt')
    if not os.path.exists(outdir_new):
        os.mkdir(outdir_new)

    to_process_djvu = []

    for rootdir, dirs, files in os.walk(indir):
        for file in files:
            if file.split('.')[-1] == 'djvu':
                to_process_djvu.append((rootdir, file))

    for rootdir, file in to_process_djvu:
        file_djvu = os.path.join(rootdir, file)
        file_txt = os.path.join(outdir_new, file[: -4] + "txt")
        os.system(f'djvutxt {file_djvu} {file_txt}')
        with open(os.path.join(outdir_new, 'djvu_converted_books.txt'), 'a+') as f:
            f.write(file_djvu + '\n')
