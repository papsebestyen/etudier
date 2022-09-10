print(f"{5}://{6}:" f"{7}@{8}:{9}" "eeee")

chrome_options.add_argument(f"--proxy-server={prefix}://{host}:{port_no}")
chrome_options.add_argument(f'--host-resolver-rules="MAP * ~NOTFOUND , EXCLUDE {host}"')
