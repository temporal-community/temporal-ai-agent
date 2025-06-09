import os
from dotenv import load_dotenv


def delete_food_ordering_products():
    """Archive all Stripe products with metadata use_case = food_ordering_demo (since products with prices cannot be deleted)."""
    import stripe
    
    # Load environment variables and configure stripe
    load_dotenv(override=True)
    stripe.api_key = os.getenv("STRIPE_API_KEY")
    
    if not stripe.api_key:
        print("Error: STRIPE_API_KEY not found in environment variables")
        return
    
    try:
        # Search for products with food_ordering_demo use_case
        products = stripe.Product.search(
            query="metadata['use_case']:'food_ordering_demo'",
            limit=100
        )
        
        if not products.data:
            print("No products found with use_case = food_ordering_demo")
            return
        
        archived_count = 0
        
        for product in products.data:
            try:
                # Archive the product (set active=False)
                stripe.Product.modify(product.id, active=False)
                print(f"Archived product: {product.name} (ID: {product.id})")
                archived_count += 1
                    
            except Exception as e:
                print(f"Error archiving product {product.name} (ID: {product.id}): {str(e)}")
        
        print(f"\nSuccessfully archived {archived_count} products")
        
    except Exception as e:
        print(f"Error searching for products: {str(e)}")


if __name__ == "__main__":
    delete_food_ordering_products()