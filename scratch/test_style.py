with open(r'C:\Users\babua\AppData\Local\Programs\Python\Python312\Lib\site-packages\streamlit_option_menu\frontend\dist\js\app.107b8ce3.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('styleObjectToString:j')
idx_j = text.rfind('j=', 0, idx)
print(text[idx_j-50:idx_j+150])
