# src/explainer.py

import google.generativeai as genai
import config
from neo4j import GraphDatabase

try:
    genai.configure(api_key=config.GOOGLE_API_KEY)
except AttributeError:
    print("ERROR: GOOGLE_API_KEY not found in config.py. Please add it.")
    exit()

class Explainer:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def close(self):
        self.driver.close()

    def get_item_category_name(self, item_id: str) -> str:
        """
        Finds the category ID for a given item ID from the graph.
        For simplicity, we'll just return the ID as its "name".
        """
        query = """
        MATCH (i:Item {id: $item_id})-[:BELONGS_TO]->(c:Category)
        RETURN c.id AS categoryId
        LIMIT 1
        """
        with self.driver.session() as session:
            result = session.run(query, item_id=int(item_id))
            record = result.single()
            return str(record["categoryId"]) if record else "a popular category"

    def generate_explanation(self, source_item_id: str, recommended_item_id: str) -> str:
        """
        Generates a human-readable explanation for a recommendation by providing
        context to an LLM.
        """
        print("Fetching context from the graph...")
        source_category = self.get_item_category_name(source_item_id)
        recommended_category = self.get_item_category_name(recommended_item_id)
        
        print("Generating explanation with LLM...")
        
        prompt = f"""
        You are a friendly and helpful e-commerce assistant. Your tone is concise and positive.
        A customer is currently looking at an item from category '{source_category}'.
        Based on our data, we are recommending an item from category '{recommended_category}'.
        
        Your task is to write a single, engaging sentence to explain this recommendation.
        
        Do NOT mention "data", "users", "sessions", or "co-occurrence". Focus on the product categories.
        
        Example: Because you're exploring items in category 1338, you might also be interested in this product from category 553!
        
        Now, generate the sentence for the user.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Could not generate explanation due to an API error: {e}"

if __name__ == "__main__":
    explainer = Explainer(config.NEO4J_URI, config.NEO4J_USER, config.NEO4J_PASSWORD)

    source_item = "285930"
    recommended_item = "8692" 

    print(f"Creating an explanation for why item '{recommended_item}' is a good recommendation for someone viewing '{source_item}'...")
    
    explanation = explainer.generate_explanation(source_item, recommended_item)
    
    print("\n" + "="*40)
    print("--- LLM-Generated Recommendation Explanation ---")
    print(f"'{explanation}'")
    print("="*40)
    
    explainer.close()