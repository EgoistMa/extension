#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parser for Baiying (百应) product selection page.
Extracts product name, commission percentage, and commission amount.

HTML Structure (based on analysis):
- Product wrapper: index_module__wrapper___dadac
  - Title: index_module__luckyTitle___dadac or index_module__oneLine___dadac
  - Price: index_module__price___dadac (到手价 ¥XX)
  - Commission rate: index_module__cosratio___dadac (e.g., "30") + index_module__percentage___dadac ("%")
  - Commission amount: index_module__cosFee___dadac (赚¥XX.X)
  - Shop name: index_module__shopName___dadac
  - Shop score: index_module__score___dadac
"""

import re
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import json


def parse_baiying_products(html_content: str) -> List[Dict[str, str]]:
    """
    Parse Baiying product selection page and extract product information.

    Args:
        html_content: The HTML content of the page

    Returns:
        List of dictionaries containing:
        - name: Product name (品名)
        - commission_rate: Commission percentage (佣金百分比)
        - commission_amount: Commission earning (佣金赚)
        - price: Product price (optional)
        - shop_name: Shop name (optional)
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    products = []

    # Find all product wrapper elements
    wrapper_elements = soup.find_all(class_=re.compile(r'index_module__wrapper___\w+'))

    for wrapper in wrapper_elements:
        # Check if this wrapper contains commission info (is a product card)
        text = wrapper.get_text()
        if '赚' not in text:
            continue

        product = {}

        # Extract product name from luckyTitle or oneLine class
        title_elem = wrapper.find(class_=re.compile(r'index_module__(luckyTitle|oneLine)___\w+'))
        if title_elem:
            product['name'] = title_elem.get_text(strip=True)

        # Extract commission rate from cosratio class
        cosratio_elem = wrapper.find(class_=re.compile(r'index_module__cosratio___\w+'))
        if cosratio_elem:
            rate = cosratio_elem.get_text(strip=True)
            product['commission_rate'] = rate + '%'

        # Extract commission amount from cosFee class
        cosfee_elem = wrapper.find(class_=re.compile(r'index_module__cosFee___\w+'))
        if cosfee_elem:
            fee_text = cosfee_elem.get_text(strip=True)
            # Extract the amount from text like "赚¥11.9"
            amount_match = re.search(r'[¥￥]?(\d+\.?\d*)', fee_text)
            if amount_match:
                product['commission_amount'] = '¥' + amount_match.group(1)

        # Extract price (optional)
        price_elem = wrapper.find(class_=re.compile(r'index_module__price___\w+'))
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            price_match = re.search(r'[¥￥](\d+\.?\d*)', price_text)
            if price_match:
                product['price'] = '¥' + price_match.group(1)

        # Extract shop name (optional)
        shop_elem = wrapper.find(class_=re.compile(r'index_module__shopName___\w+'))
        if shop_elem:
            product['shop_name'] = shop_elem.get_text(strip=True)

        # Extract monthly sales (月销)
        sales_elem = wrapper.find(class_=re.compile(r'index_module__priceAndSales___\w+'))
        if sales_elem:
            sales_text = sales_elem.get_text(strip=True)
            sales_match = re.search(r'月销\s*([\d,]+)', sales_text)
            if sales_match:
                product['monthly_sales'] = sales_match.group(1).replace(',', '')

        # Extract shop score (店铺评分)
        score_elem = wrapper.find(class_=re.compile(r'index_module__score___\w+'))
        if score_elem:
            product['shop_score'] = score_elem.get_text(strip=True)

        # Only add if we have meaningful data
        if product.get('name') and (product.get('commission_amount') or product.get('commission_rate')):
            products.append(product)

    return products


def format_output(products: List[Dict[str, str]], include_optional: bool = False) -> str:
    """Format the output as a table."""
    if not products:
        return "No products found."

    output = []
    output.append("-" * 90)

    if include_optional:
        output.append(f"{'品名':<35} {'佣金百分比':<12} {'佣金赚':<10} {'价格':<10} {'店铺':<15}")
    else:
        output.append(f"{'品名':<45} {'佣金百分比':<15} {'佣金赚':<15}")

    output.append("-" * 90)

    for p in products:
        name = p.get('name', 'N/A')
        # Truncate name if too long
        if len(name) > 40:
            name = name[:37] + '...'

        rate = p.get('commission_rate', 'N/A')
        amount = p.get('commission_amount', 'N/A')

        if include_optional:
            price = p.get('price', 'N/A')
            shop = p.get('shop_name', 'N/A')[:12]
            output.append(f"{name:<35} {rate:<12} {amount:<10} {price:<10} {shop:<15}")
        else:
            output.append(f"{name:<45} {rate:<15} {amount:<15}")

    output.append("-" * 90)
    output.append(f"Total: {len(products)} products")

    return '\n'.join(output)


def get_products_as_list(products: List[Dict[str, str]]) -> List[tuple]:
    """
    Convert products to a simple list of tuples.

    Returns:
        List of tuples: (品名, 佣金百分比, 佣金赚)
    """
    return [
        (
            p.get('name', ''),
            p.get('commission_rate', ''),
            p.get('commission_amount', '')
        )
        for p in products
    ]


if __name__ == '__main__':
    import sys
    import io

    # Fix encoding for Windows console
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    # Read the sample file
    sample_file = r'c:\Users\EGOIST\Documents\extension\samplebaiying-html-page.html'

    try:
        with open(sample_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        print("=" * 60)
        print("Parsing Baiying Products")
        print("=" * 60)

        products = parse_baiying_products(html_content)
        print(f"\nFound {len(products)} products\n")

        # Display results
        print(format_output(products))

        # Show JSON output
        print("\n\nJSON Output (first 5 products):")
        print(json.dumps(products[:5], ensure_ascii=False, indent=2))

        if len(products) > 5:
            print(f"... and {len(products) - 5} more products")

        # Show as simple list
        print("\n\nSimple list format (first 10):")
        simple_list = get_products_as_list(products)
        for i, (name, rate, amount) in enumerate(simple_list[:10], 1):
            print(f"{i}. {name[:40]} | {rate} | {amount}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
