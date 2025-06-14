import json
import os

from dotenv import load_dotenv


def create_stripe_products():
    """Create Stripe products and prices from the stripe_pizza_products.json file."""
    import stripe

    # Load environment variables and configure stripe
    load_dotenv(override=True)
    stripe.api_key = os.getenv("STRIPE_API_KEY")

    if not stripe.api_key:
        print("Error: STRIPE_API_KEY not found in environment variables")
        return

    # Load the products data
    current_dir = os.path.dirname(__file__)
    products_file = os.path.join(current_dir, "stripe_pizza_products.json")

    with open(products_file, "r") as f:
        products_data = json.load(f)

    # Filter for food ordering demo products only
    food_products = [
        p
        for p in products_data
        if p.get("metadata", {}).get("use_case") == "food_ordering_demo"
    ]

    created_products = []

    for product_data in food_products:
        try:
            # Create the product with relevant fields
            product = stripe.Product.create(
                name=product_data["name"],
                description=product_data.get("description"),
                images=product_data.get("images", []),
                metadata=product_data.get("metadata", {}),
                type=product_data.get("type", "service"),
                active=product_data.get("active", True),
            )

            # Create price for the product if price_info exists
            price_info = product_data.get("price_info")
            if price_info:
                price_amount = price_info.get("amount")
                currency = price_info.get("currency", "usd")

                price = stripe.Price.create(
                    currency=currency, unit_amount=price_amount, product=product.id
                )

                # Set this price as the default price for the product
                stripe.Product.modify(product.id, default_price=price.id)

                print(
                    f"Created product: {product.name} (ID: {product.id}) with default price ${price_amount/100:.2f}"
                )

                created_products.append(
                    {
                        "name": product.name,
                        "id": product.id,
                        "price_id": price.id,
                        "price_amount": price_amount,
                        "original_id": product_data["id"],
                    }
                )
            else:
                print(
                    f"Created product: {product.name} (ID: {product.id}) - No price defined"
                )
                created_products.append(
                    {
                        "name": product.name,
                        "id": product.id,
                        "original_id": product_data["id"],
                    }
                )

        except Exception as e:
            print(f"Error creating product {product_data['name']}: {str(e)}")

    print(f"\nSuccessfully created {len(created_products)} products with prices")
    return created_products


if __name__ == "__main__":
    create_stripe_products()
