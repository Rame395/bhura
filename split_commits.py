filepath = 'd:/bhura/bhurats/frontend/checkout.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Revert the header fix
fixed = '<div class="hidden sm:block text-[11px] font-mono tracking-widest uppercase text-bhuraTextGrey">Secure Checkout'
orig = '<div class="text-[11px] font-mono tracking-widest uppercase text-bhuraTextGrey">Secure Checkout'

content = content.replace(fixed, orig)
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
