def get_filtered_file_list(extensions, src_dir):
    file_list = []
    for ext in extensions:
        file_list.extend(src_dir.glob(f'**/*{ext}'))
    return file_list
