with open(r'C:\Users\babua\AppData\Local\Programs\Python\Python312\Lib\site-packages\streamlit_option_menu\frontend\dist\js\app.107b8ce3.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('styles["icon"]')
print("Found styles['icon'] at:", idx)
if idx != -1:
    print(text[idx-100:idx+250])
else:
    for m in range(len(text)):
        if text[m:m+6] == 'styles':
            print(text[m:m+50])
