import json

with open('exports/export_target_20251015_143552.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Sample image_urls from scraped products:\n")
for i, product in enumerate(data[:5], 1):
    print(f"{i}. Product {product['product_id']} - {product.get('title', 'N/A')[:50]}")
    images = product.get('image_urls')
    if images:
        if isinstance(images, str):
            imgs = json.loads(images) if images.startswith('[') else [images]
        else:
            imgs = images
        print(f"   Images ({len(imgs)} found):")
        for img in imgs[:3]:
            print(f"     - {img}")
    else:
        print(f"   No images")
    print()

