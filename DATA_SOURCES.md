# Data Sources

This prototype uses **Kaggle** and **Apify** instead of Trustpilot (no Trustpilot API key needed).

## Kaggle

| Industry      | Dataset                                                               |
|---------------|-----------------------------------------------------------------------|
| ride-sharing  | [jschne61701/uber-rides-costumer-reviews-dataset](https://www.kaggle.com/datasets/jschne61701/uber-rides-costumer-reviews-dataset) |
| food-delivery | [skamlo/food-delivery-apps-reviews](https://www.kaggle.com/datasets/skamlo/food-delivery-apps-reviews) |
| e-commerce    | [yasserh/amazon-product-reviews-dataset](https://www.kaggle.com/datasets/yasserh/amazon-product-reviews-dataset) |
| restaurants   | [omkarsabnis/yelp-reviews-dataset](https://www.kaggle.com/datasets/omkarsabnis/yelp-reviews-dataset) |

## Apify (G2, Capterra, Trustpilot)

For industries without Kaggle datasets, Apify fetches reviews from G2, Capterra, Trustpilot:

| Industry   | Companies                          | Data source      |
|------------|------------------------------------|------------------|
| hospitality| Yelp, TripAdvisor, OpenTable       | Apify / Scraping |
| banking    | Revolut, N26, Chime                | Apify / Scraping |
| healthcare | Zocdoc, Healthgrades, WebMD        | Apify / Scraping |
| travel     | Booking.com, Airbnb, Expedia       | Apify / Kaggle   |
| telecom    | Vodafone, Verizon, AT&T           | Apify / Scraping |
| insurance  | Lemonade, Geico, Allstate          | Apify / Scraping |

**Setup**

1. Create account at [kaggle.com](https://kaggle.com)
2. API → Create New Token → download `kaggle.json`
3. Place in `~/.kaggle/kaggle.json` (or `%USERPROFILE%\.kaggle\kaggle.json` on Windows)
4. `pip install kaggle`

Datasets are downloaded to `data/kaggle/` on first use.

## Apify

For G2, Capterra, and Trustpilot reviews (CRM, SaaS industries):

1. Create account at [apify.com](https://apify.com)
2. Get API token from Settings → Integrations
3. Add to `.env`: `APIFY_API_TOKEN=apify_api_...`

Or pass in request: `resource_keys: {"apify": "apify_api_..."}`

## Local Sample Data

When Kaggle/Apify are not configured, the system uses local JSON files:

- `data/sample_reviews.json` (CRM)
- `data/sample_reviews_food.json`
- `data/sample_reviews_ride.json`
- `data/sample_reviews_saas.json`
- `data/sample_reviews_ecommerce.json`
- `data/sample_reviews_restaurants.json`
- `data/sample_reviews_hospitality.json`
- `data/sample_reviews_banking.json`
- `data/sample_reviews_healthcare.json`
- `data/sample_reviews_travel.json`
- `data/sample_reviews_telecom.json`
- `data/sample_reviews_insurance.json`

## Web Scrapers

Scrapers in `resources/scrapers/` (G2, Capterra, generic) attempt HTML/JSON extraction when Apify is not configured. G2 and Capterra are JS-heavy; prefer Apify for production.
