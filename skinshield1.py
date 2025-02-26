import streamlit as st
import pandas as pd
import os
import re
import base64

# Function to validate email
def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

# Function to validate non-numeric input
def is_valid_non_numeric(text):
    return not any(char.isdigit() for char in text)

# Function to calculate allergy probability
def calculate_allergy_probability(file_path, email_id, product_name, product_components, previous_allergens, skin_type):
    df = pd.read_excel(file_path) if os.path.exists(file_path) else pd.DataFrame()
    df.columns = [col.strip().lower() for col in df.columns]

    normalized_components = [component.strip().lower() for component in product_components]

    prior_allergic = 0.5
    prior_not_allergic = 1 - prior_allergic

    likelihood_allergic = 1.0
    likelihood_not_allergic = 1.0

    for allergen in previous_allergens:
        if allergen.lower() in normalized_components:
            likelihood_allergic *= 0.8
            likelihood_not_allergic *= 0.2

    if skin_type.lower() in ['sensitive', 'dry']:
        likelihood_allergic *= 1.2
        likelihood_not_allergic *= 0.8

    if not df.empty and email_id in df['email id'].values:
        user_data = df[df['email id'] == email_id]
        for component in normalized_components:
            if component in user_data.columns:
                component_value = user_data[component].values[0]
                if component_value == 1:
                    likelihood_allergic *= 0.9
                    likelihood_not_allergic *= 0.1
                elif component_value == 0.5:
                    likelihood_allergic *= 0.5
                    likelihood_not_allergic *= 0.5
                elif component_value == 0:
                    likelihood_allergic *= 0.1
                    likelihood_not_allergic *= 0.9

    numerator = likelihood_allergic * prior_allergic
    denominator = numerator + (likelihood_not_allergic * prior_not_allergic)

    probability_allergic = numerator / denominator if denominator != 0 else 0
    return round(probability_allergic * 100, 2)

# Dermatologist suggestion based on skin type and components
def dermatologist_suggestions(skin_type, product_components):
    skin_type = skin_type.lower()
    recommendations = []

    # Skin type-based suggestions
    if skin_type == "normal":
        recommendations.append("For Normal skin: You can use most products, but avoid overly oily or greasy formulations.")
    elif skin_type == "oily":
        recommendations.append("For Oily skin: Look for oil-free and non-comedogenic products. Avoid products with heavy oils like coconut oil.")
    elif skin_type == "dry":
        recommendations.append("For Dry skin: Hydrating and moisturizing products are recommended. Avoid products with alcohol or astringents.")
    elif skin_type == "sensitive":
        recommendations.append("For Sensitive skin: Avoid fragrances and harsh ingredients. Opt for products with gentle, soothing ingredients like Aloe Vera.")

    # Product component-based suggestions
    sensitive_ingredients = ['alcohol', 'fragrance', 'parabens', 'sulfates']
    if any(ingredient in [component.lower() for component in product_components] for ingredient in sensitive_ingredients):
        recommendations.append("Warning: This product contains ingredients like alcohol, parabens, or sulfates that may irritate sensitive skin.")

    # Add more specific suggestions for certain ingredients (for example, Vitamin C or Retinol)
    if 'vitamin c' in [component.lower() for component in product_components]:
        recommendations.append("Vitamin C can brighten and even out skin tone, but it may cause irritation for sensitive skin.")
    if 'retinol' in [component.lower() for component in product_components]:
        recommendations.append("Retinol is effective for anti-aging, but can be drying and irritating for dry or sensitive skin. Use with caution.")

    return recommendations

# Function to set background image
def set_background(image_file):
    with open(image_file, "rb") as image:
        encoded_image = base64.b64encode(image.read()).decode()
    bg_image_style = f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{encoded_image}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }}
    </style>
    """
    st.markdown(bg_image_style, unsafe_allow_html=True)

# Set the background image
set_background("C:\\Users\\DELL\\OneDrive\\Desktop\\app_bg.jpg")  # Update path for the background image

# Title and Subtitle with Black Bold Styling
st.markdown(
    """
    <style>
    .title {
        color: black;
        font-size: 3.5rem;
        text-align: center;
        font-weight: bold;
        text-shadow: 1px 1px 2px rgba(200, 200, 200, 0.5); /* Optional subtle shadow */
    }
    .subtitle {
        color: black;
        font-size: 2rem;
        text-align: center;
        font-weight: bold;
        margin-bottom: 20px;
    }
    </style>
    <div>
        <h1 class="title">SKINSHIELD</h1>
        <h2 class="subtitle">Predicting Allergies for Safer Beauty</h2>
    </div>
    """, 
    unsafe_allow_html=True
)

# File path for the dataset
file_path = "C:\\Users\\DELL\\OneDrive\\Desktop\\Book2.xlsx"  # Update the path for your Excel file

# Ensure the file has required columns
if not os.path.exists(file_path):
    df = pd.DataFrame(columns=['Sl No', 'name', 'email id', 'previous_allergens', 'skin type'])
    df.to_excel(file_path, index=False)

is_registered = st.radio("Already registered?", ("Yes", "No"))

valid_inputs = True  # Initialize validation flag

# Use session_state to store the suggestions
if 'suggestions' not in st.session_state:
    st.session_state.suggestions = []

if is_registered == "Yes":
    email_id = st.text_input("Enter your email ID:")
    if email_id and not is_valid_email(email_id):
        st.error("Enter a valid email ID.")
        valid_inputs = False

    product_name = st.text_input("Enter the name of the new product:")
    if product_name and not is_valid_non_numeric(product_name):
        st.error("Product name should not contain numbers.")
        valid_inputs = False

    product_components = st.text_area("List the components of the new product (comma-separated):", placeholder="e.g., Vitamin C, Aloe Vera")
    if product_components and not all(is_valid_non_numeric(component) for component in product_components.split(',')):
        st.error("Product components should not contain numbers.")
        valid_inputs = False

    if product_components and st.button("Calculate Allergy Probability") and valid_inputs:
        try:
            df = pd.read_excel(file_path)
            df.columns = [col.strip().lower() for col in df.columns]
            if 'email id' not in df.columns:
                st.error("The 'email id' column is missing in the dataset.")
            user_data = df[df['email id'] == email_id]
            if user_data.empty:
                st.error("User not found. Please register first.")
            else:
                previous_allergens = user_data['previous_allergens'].values[0]
                if isinstance(previous_allergens, str):
                    previous_allergens = previous_allergens.split(',')  # Ensure the allergens are split properly
                else:
                    previous_allergens = []
                skin_type = user_data['skin type'].values[0] if 'skin type' in user_data.columns else "Normal"
                probability = calculate_allergy_probability(file_path, email_id, product_name, product_components.split(','), previous_allergens, skin_type)

                st.success(f"The probability of being allergic to {product_name} is {probability}%.")
                if probability < 35:
                    st.info("This product has *unlikely sensitization to the allergen.*")
                elif 35 <= probability < 70:
                    st.warning("This product has *doubtful significance.*")
                else:
                    st.error("This product has a *greater possibility of allergic reaction.*")
                
                # Store suggestions in session state
                st.session_state.suggestions = dermatologist_suggestions(skin_type, product_components.split(','))

        except Exception as e:
            st.error(f"Error: {e}")

    # Show dermatologist suggestions when the button is clicked
    if st.button("View Suggestions"):
        if st.session_state.suggestions:
            st.write("\n### Dermatologist Suggestions:")
            for suggestion in st.session_state.suggestions:
                st.write(f"- {suggestion}")
        else:
            st.warning("Please calculate the allergy probability first.")
else:
    email_id = st.text_input("Enter your email ID:")
    if email_id and not is_valid_email(email_id):
        st.error("Enter a valid email ID.")
        valid_inputs = False

    user_name = st.text_input("Enter your name:")
    if user_name and not is_valid_non_numeric(user_name):
        st.error("Name should not contain numbers.")
        valid_inputs = False

    previous_allergens = st.text_area("Enter the allergens you are sensitive to (comma-separated):", placeholder="e.g., Pollen, Peanuts, Dust")
    if previous_allergens and not all(is_valid_non_numeric(allergen) for allergen in previous_allergens.split(',')):
        st.error("Allergen names should not contain numbers.")
        valid_inputs = False

    skin_type = st.selectbox("Select your skin type:", ["Normal", "Oily", "Dry", "Sensitive"])
    product_name = st.text_input("Enter the name of the new product:")
    if product_name and not is_valid_non_numeric(product_name):
        st.error("Product name should not contain numbers.")
        valid_inputs = False

    product_components = st.text_area("List the components of the new product (comma-separated):", placeholder="e.g., Vitamin C, Aloe Vera")
    if product_components and not all(is_valid_non_numeric(component) for component in product_components.split(',')):
        st.error("Product components should not contain numbers.")
        valid_inputs = False

    if st.button("Register and Calculate Allergy Probability") and valid_inputs:
        try:
            if os.path.exists(file_path):
                df = pd.read_excel(file_path)
                df.columns = [col.strip().lower() for col in df.columns]
            else:
                df = pd.DataFrame(columns=['sl no', 'name', 'email id', 'previous_allergens', 'skin type'])

            if email_id in df['email id'].values:
                st.warning("Email ID already exists. Using existing data for calculations.")
            else:
                new_sl_no = df['sl no'].max() + 1 if 'sl no' in df.columns and not df.empty else 1
                new_entry = pd.DataFrame([{
                    'sl no': new_sl_no,
                    'name': user_name,
                    'email id': email_id,
                    'previous_allergens': previous_allergens,
                    'skin type': skin_type
                }])
                df = pd.concat([df, new_entry], ignore_index=True)

            df.to_excel(file_path, index=False)

            probability = calculate_allergy_probability(file_path, email_id, product_name, product_components.split(','), previous_allergens.split(','), skin_type)
            st.success(f"Registration complete! The probability of being allergic to {product_name} is {probability}%.")
            if probability < 35:
                st.info("This product has *unlikely sensitization to the allergen.*")
            elif 35 <= probability < 70:
                st.warning("This product has *doubtful significance.*")
            else:
                st.error("This product has a *greater possibility of allergic reaction.*")
            
            # Store suggestions in session state
            st.session_state.suggestions = dermatologist_suggestions(skin_type, product_components.split(','))

        except Exception as e:
            st.error(f"Error: {e}")

    # Show dermatologist suggestions when the button is clicked
    if st.button("View Suggestions"):
        if st.session_state.suggestions:
            st.write("\n### Dermatologist Suggestions:")
            for suggestion in st.session_state.suggestions:
                st.write(f"- {suggestion}")
        else:
            st.warning("Please calculate the allergy probability first.")

# TO RUN THE APP NAVIGATE TO THE CURRECT FOLDER IN TERMINAL AND TYPE stremlit run app.py in this case streamlit run skinshiled1.py