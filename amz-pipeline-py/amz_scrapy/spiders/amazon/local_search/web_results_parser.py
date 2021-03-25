import os
import re

from scrapy.selector import Selector
from six.moves import urllib

from bb_utils.text.parsers import to_naive_date, re_group, to_float, to_int, to_usd_price

_script_dir = os.path.dirname(os.path.realpath(__file__))
_research_dir = os.path.join(_script_dir, 'research')


def find_widget_name(prod_el):
    widget_heading = prod_el.xpath(
        (
            "./ancestor::*[contains(@class, 's-shopping-adviser')]"
            "/*[contains(@class, 's-shopping-adviser-heading')]//h3//text()"
        )).extract()

    widget_heading = " ".join(widget_heading)
    widget_heading = " ".join(widget_heading.split()).strip()
    widget_heading_lc = widget_heading.lower()

    if "amazon's choice" in widget_heading_lc:
        widget_heading = "Amazon's Choice"
    if "editorial recommendations" in widget_heading_lc:
        widget_heading = "Editorial recommendations"

    return widget_heading



def add_widget_attributes(prod_el, product):
    card_classes = prod_el.xpath("./@class").get("")
    if "s-inner-result-item" in card_classes:
        product["in_widget"] = True

    card_header = prod_el.xpath(".//*[contains(@class, 's-product-header')]//text()").extract()
    header = " ".join(" ".join(card_header).split()).strip()
    if header:
        header = header.lstrip('"').rstrip('"')
        product["card_header"] = header

    widget_name = find_widget_name(prod_el)
    if widget_name:
        product["widget_name"] = widget_name
        product["in_widget"] = True


# TODO: Reviews, availability, byLine
def parse_product_card(prod_el):
    product = {}

    asin = prod_el.xpath('@data-asin').extract_first()
    if not asin:
        return None
    product['asin'] = asin

    title = (' '.join(prod_el.xpath('.//*/h2//text()').extract())).strip()
    product['title'] = ' '.join(title.split())
    if not product['title']:
        return None

    image = prod_el.xpath('.//img[1]/@src').extract_first('')
    if image.startswith('http'):
        product['image'] = image

    product['is_sponsored'] = len(
        prod_el.xpath('.//*[@data-component-type="sp-sponsored-result"]')) > 0

    product['has_prime_badge'] = len(
        prod_el.xpath('.//*[@aria-label="Amazon Prime"]')) > 0
    if not product['has_prime_badge']:
        # Amazon does not always show "prime" badge for anonymous users, but such products may have some other text
        # pointing that the product is Prime-eligible. At least false negatives are possible.
        #
        # Example: FREE Shipping on your first order shipped by Amazon
        maybe_prime_text = prod_el.xpath('.//*[@class="a-row"]//*[contains(text(), "FREE Shipping")]//text()').extract_first("").strip()
        if maybe_prime_text:
            product['has_prime_badge'] = True
            product['prime_badge_guessed'] = True

    prices_el = prod_el.xpath('.//span[contains(@class, "a-price")]')
    if len(prices_el) > 0:
        product['buy_price'] = to_usd_price(
            prices_el.xpath(
                './/span[contains(@class, "a-offscreen")][1]/text()').
            extract_first())
        list_price = to_usd_price(
            prices_el.xpath(
                './/span[@aria-hidden="true"][1]/text()').
            extract_first())
        if list_price:
            product['list_price'] = list_price

    badge_text_list = []
    for badge_el in prod_el.xpath(".//*[@class='a-badge-label']"):
        badge_text = ' '.join(badge_el.xpath(".//text()").extract())
        badge_text = ' '.join(badge_text.split()).strip()
        if badge_text:
            badge_text_list.append(badge_text)
    if badge_text_list:
        product["badges"] = badge_text_list

    coupon_text = prod_el.xpath('.//span[contains(@class, "s-coupon-highlight-color")]//text()').extract_first("").strip()
    if coupon_text:
        product["coupon_text"] = coupon_text

    amazon_choice_badge = prod_el.xpath('.//*[@aria-label="Amazon\'s Choice"]')
    if len(amazon_choice_badge):
        product['has_amazon_choice_badge'] = True

    product['url'] = prod_el.xpath(
        './/a[contains(@class, "a-link-normal")][1]/@href').extract_first('')

    if product['url']:
        url_unquoted = urllib.parse.unquote_plus(product['url'])
        match = re.search(r'sr=(\d+)\-(\d+)(?:-\w+)?(?:&|$)', url_unquoted)
        if match:
            product['sr_pos'] = to_int(match.group(2))

    parse_availability(prod_el, product)

    parse_reviews(prod_el, product)

    add_widget_attributes(prod_el, product)

    return product


def parse_reviews(prod_el, product):
    # Example: 4.0 out of 5 stars
    rating_text = prod_el.xpath(
        './/*[contains(@class, "a-icon-star-small")]//text()').extract_first(
            '').strip()
    rating = to_float(re_group(rating_text, r'([\S]+) out of 5'))
    if rating:
        product['review_rating'] = rating

    review_count_text = ''.join(
        prod_el.xpath('.//a[contains(@href, "#customerReviews")]//text()').
        extract()).strip()
    review_count = to_int(review_count_text)
    if review_count:
        product['review_count'] = review_count


def parse_availability(prod_el, product):
    # Try to get delivery data from FREE Delivery label.
    # Example:
    # - FREE Delivery by <Wed, Oct 23> for Prime members
    # - FREE Delivery <Tue, Oct 22>
    get_it_by_text = prod_el.xpath(
        './/*[starts-with(@aria-label, "FREE Delivery")]//'
        'span[@class="a-text-bold"]/text()').extract_first('').strip()
    if get_it_by_text:
        product['get_it_by_text'] = get_it_by_text

    # If "Get it" label is available, use the date from it.
    # Example:
    # - Get it as soon as <Tomorrow, Oct 18>
    # - Get it <Tomorrow, Oct 19>
    get_it_by_text = prod_el.xpath(
        './/*[starts-with(@aria-label, "Get it")]//'
        'span[@class="a-text-bold"]/text()').extract_first('').strip()
    if get_it_by_text:
        product['get_it_by_text'] = get_it_by_text

    if product.get('get_it_by_text'):
        date_s = product['get_it_by_text']
        date_s = date_s.replace('Tomorrow, ', '')
        date_s = date_s.replace('Today, ', '')
        product['get_it_by_date'] = to_naive_date(date_s)

    # Example:
    # - Only 9 left in stock - order soon.
    stock_count_msg = prod_el.xpath(
        './/*[contains(@aria-label, "left in stock")]/@aria-label'
    ).extract_first('').strip()
    if stock_count_msg:
        stock_count = to_int(
            re_group(stock_count_msg, r'Only (\d+) left in stock'))
        if stock_count:
            product['stock_count'] = stock_count

    # Example: Temporarily out of stock.
    if not stock_count_msg:
        stock_count_msg = prod_el.xpath(
            './/*[contains(@aria-label, "out of stock")]/@aria-label'
        ).extract_first('').strip()
        if stock_count_msg:
            product['stock_count'] = 0


def extract_internal_vars(sel):
    feedback_form = sel.xpath('//form[contains(@action, "hmsfeedback")]')
    triggered_weblabs = feedback_form.xpath(
        './input[@name="triggeredWeblabs"]/@value').extract_first()
    customer_city = feedback_form.xpath(
        './input[@name="customerCity"]/@value').extract_first()
    query_id = feedback_form.xpath(
        './input[@name="queryId"]/@value').extract_first()
    marketplace_id = feedback_form.xpath(
        './input[@name="marketplaceId"]/@value').extract_first()
    country_code = feedback_form.xpath(
        './input[@name="countryCode"]/@value').extract_first()
    customer_zip_code = feedback_form.xpath(
        './input[@name="customerZipCode"]/@value').extract_first()
    device = feedback_form.xpath(
        './input[@name="device"]/@value').extract_first()
    store = feedback_form.xpath(
        './input[@name="store"]/@value').extract_first()

    # This does not seem to be available as of 2019-12-31
    if customer_zip_code:
        return {
            'triggered_weblabs': triggered_weblabs,
            'customer_city': customer_city,
            'query_id': query_id,
            'marketplace_id': marketplace_id,
            'country_code': country_code,
            'customer_zip_code': customer_zip_code,
            'device': device,
            'store': store
        }
    else:
        return {}


def extract_related_searches(sel):
    keywords = set()
    for link in sel.xpath("*//a[starts-with(@href, '/s/?k=')]/@href").extract():
        keyword = re_group(link, r"/s/\?k=([\w\+]+)")
        if keyword:
            keyword = keyword.replace("+", " ").strip()
            keywords.add(keyword)
    return keywords


def extract_metadata(sel, html, initial_metadata):
    total_results = to_int(
        re_group(html, r'\"totalResultCount\"\s*:\s*(\d+)', '').strip())

    asins_on_page = to_int(
        re_group(html, r'\"asinOnPageCount\"\s*:\s*(\d+)', '').strip())

    search_alias = re_group(html, r'\"searchAlias\"\s*:\s*\"(\w+)\"',
                            '').strip()

    keywords = re_group(html, r'\"keywords\"\s*:\s*\"([^\"]+)\"', '').strip()

    internal_vars = extract_internal_vars(sel)

    metadata = initial_metadata
    metadata.update({
        'total_results': total_results,
        'asins_on_page': asins_on_page,
        'search_alias': search_alias,
        'keywords': keywords,
        'internal': internal_vars,
    })

    first_rank = None

    # Example:
    # - 1-48 of over 10,000 results for "chest box for boys"
    # - 1-48 of 75 results for "sambo shoes"
    total_results_text = sel.xpath(
        '//*[@data-component-type="s-result-info-bar"]//'
        '*[contains(text(), "results for")]/text()').extract_first('')
    match = re.match(r'([\S]+)-([\S]+)\sof\s(?:over\s)?([\S]+)\sresults',
                     total_results_text)
    if match:
        first_rank = to_int(match.group(1))
        last_rank = to_int(match.group(2))
        total_results_est = to_int(match.group(3))

        if first_rank:
            metadata['first_rank'] = first_rank
            metadata['last_rank'] = last_rank
            metadata['total_results_est'] = total_results_est

    return metadata


def parse_search_results_html(html):
    sel = Selector(text=html)
    return parse_search_results(html, sel)


def parse_products(sel):
    prod_elms = sel.xpath(
        '//*[contains(@class, "s-result-list")]//*[@data-asin]')
    for prod_el in prod_elms:
        product = parse_product_card(prod_el)

        if product is None:
            continue

        yield product


def parse_search_results(html, sel):
    sel = Selector(text=html)
    result = {}

    num_sponsored = 0
    num_products = 0

    first_rank = None

    products = []
    for product in parse_products(sel):
        products.append(product)

        num_products += 1

        if product['is_sponsored']:
            num_sponsored += 1

        if first_rank is None and product.get('sr_pos') is not None:
            first_rank = product.get('sr_pos') - len(products)        

    metadata = extract_metadata(sel, html, {'first_rank': first_rank})
    metadata['parser'] = {
        'version': 'web.20191017.1.1',
        'num_products': num_products,
        'num_sponsored': num_sponsored
    }

    result['meta'] = metadata
    result['products'] = products
    result['related_searches'] = list(extract_related_searches(sel))

    return result


def ad_hoc_test():
    import os
    from pprint import pprint

    file_path = os.path.join(_research_dir,
                             '20201031/Amazon.com _ carabiner clip.html')
    print(os.path.abspath(file_path))

    html = None
    with open(file_path, 'r') as content_file:
        html = content_file.read()

    parsed = parse_search_results_html(html)
    pprint(parsed)


if __name__ == '__main__':
    ad_hoc_test()
