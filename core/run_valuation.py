from startup_valuation import perform_startup_valuation

def main():
    # Example user prompt for a startup valuation
    user_prompt = """I want to valuate my startup. It is at the 'Development' stage. 
    We are building a revolutionary AI-powered cat toy. We project FCF of [60000, 90000, 150000] 
    for the next 3 years, with survival rates of [0.9,0.8,0.7]. We think WACC is around 22%. 
    Our final year EBITDA for DCF multiple might be 180000 and industry multiple is 7. 
    For VC, exit EBITDA could be 250000 with a multiple of 8 in 5 years. 
    We have a strong team (score 1.2 for scorecard), great product (score 1.3), 
    and good market opportunity (score 1.1). Other scorecard factors are average (1.0). 
    Avg pre-money for dev stage is $3M. Max checklist valuation is $8M, 
    idea quality 80, product/IP 85, team 90, operating stage 70, strategic relations 60."""

    # Your Groq API key - Replace with your actual API key
    api_key = "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"

    print("Starting startup valuation process...")
    print("\nUser Input:")
    print(user_prompt)
    print("\nProcessing valuation...")

    # Perform the valuation
    result = perform_startup_valuation(user_prompt, api_key)

    # Print the results
    print("\nValuation Results:")
    print("=" * 50)
    print(result["final_response"])
    print("=" * 50)

    # Print conversation results for debugging if needed
    print("\nDetailed Function Calls:")
    for idx, call in enumerate(result["conversation_results"], 1):
        print(f"\nCall {idx}:")
        print(f"Function: {call['function']}")
        print(f"Arguments: {call['arguments']}")
        print(f"Response: {call['response']}")

if __name__ == "__main__":
    main() 