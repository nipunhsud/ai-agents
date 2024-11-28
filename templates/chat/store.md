
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gift Recommendation Assistant</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
        
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #f6f8fd 0%, #f1f4f9 100%);
        }

        .form-container {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
        }

        .input-field {
            transition: all 0.3s ease;
        }

        .input-field:focus {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .section-card {
            transition: all 0.3s ease;
        }

        .section-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
        }

        .gradient-button {
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
            transition: all 0.3s ease;
        }

        .gradient-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
        }
    </style>
</head>
<body class="min-h-screen py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-4xl mx-auto form-container rounded-2xl shadow-2xl p-8 mb-12">
        <div class="text-center mb-12">
            <h1 class="text-4xl font-bold text-gray-800 mb-4 bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-purple-600">
                Gift Recommendation Assistant
            </h1>
            <p class="text-lg text-gray-600">Let us help you find the perfect gift! ✨</p>
        </div>

        <form id="giftForm" class="space-y-8">
            <!-- Recipient Information -->
            <div class="section-card bg-white rounded-xl p-6 shadow-lg border border-gray-100">
                <h2 class="text-2xl font-semibold text-gray-800 mb-6 flex items-center">
                    <span class="bg-indigo-100 text-indigo-600 p-2 rounded-lg mr-3">👤</span>
                    Recipient Information
                </h2>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Recipient's Name</label>
                        <input type="text" name="name" required
                            class="input-field w-full px-4 py-3 rounded-lg border border-gray-200 focus:border-indigo-500 focus:ring focus:ring-indigo-200 focus:ring-opacity-50">
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Age</label>
                        <input type="number" name="age" min="0" max="120" required
                            class="input-field w-full px-4 py-3 rounded-lg border border-gray-200 focus:border-indigo-500 focus:ring focus:ring-indigo-200 focus:ring-opacity-50">
                    </div>

                    <div class="md:col-span-2">
                        <label class="block text-sm font-medium text-gray-700 mb-2">Relationship to Recipient</label>
                        <select name="relationship" required
                            class="input-field w-full px-4 py-3 rounded-lg border border-gray-200 focus:border-indigo-500 focus:ring focus:ring-indigo-200 focus:ring-opacity-50 bg-white">
                            <option value="">Select relationship</option>
                            <option value="family">Family Member</option>
                            <option value="friend">Friend</option>
                            <option value="colleague">Colleague</option>
                            <option value="significant_other">Significant Other</option>
                            <option value="other">Other</option>
                        </select>
                    </div>
                </div>
            </div>

            <!-- Interests & Preferences -->
            <div class="section-card bg-white rounded-xl p-6 shadow-lg border border-gray-100">
                <h2 class="text-2xl font-semibold text-gray-800 mb-6 flex items-center">
                    <span class="bg-purple-100 text-purple-600 p-2 rounded-lg mr-3">💝</span>
                    Interests & Preferences
                </h2>
                
                <div class="space-y-6">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Hobbies & Interests</label>
                        <textarea name="interests" rows="3" required
                            class="input-field w-full px-4 py-3 rounded-lg border border-gray-200 focus:border-indigo-500 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
                            placeholder="e.g., reading, cooking, sports, technology..."></textarea>
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Favorite Brands or Stores (optional)</label>
                        <input type="text" name="brands"
                            class="input-field w-full px-4 py-3 rounded-lg border border-gray-200 focus:border-indigo-500 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
                            placeholder="e.g., Nike, Apple, Amazon...">
                    </div>
                </div>
            </div>

            <!-- Gift Parameters -->
            <div class="section-card bg-white rounded-xl p-6 shadow-lg border border-gray-100">
                <h2 class="text-2xl font-semibold text-gray-800 mb-6 flex items-center">
                    <span class="bg-pink-100 text-pink-600 p-2 rounded-lg mr-3">🎁</span>
                    Gift Parameters
                </h2>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Budget Range</label>
                        <select name="budget" required
                            class="input-field w-full px-4 py-3 rounded-lg border border-gray-200 focus:border-indigo-500 focus:ring focus:ring-indigo-200 focus:ring-opacity-50 bg-white">
                            <option value="">Select budget range</option>
                            <option value="under25">Under $25</option>
                            <option value="25-50">$25 - $50</option>
                            <option value="50-100">$50 - $100</option>
                            <option value="100-200">$100 - $200</option>
                            <option value="200plus">$200+</option>
                        </select>
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Occasion</label>
                        <select name="occasion" required
                            class="input-field w-full px-4 py-3 rounded-lg border border-gray-200 focus:border-indigo-500 focus:ring focus:ring-indigo-200 focus:ring-opacity-50 bg-white">
                            <option value="">Select occasion</option>
                            <option value="birthday">Birthday</option>
                            <option value="christmas">Christmas</option>
                            <option value="anniversary">Anniversary</option>
                            <option value="graduation">Graduation</option>
                            <option value="wedding">Wedding</option>
                            <option value="other">Other</option>
                        </select>
                    </div>

                    <div class="md:col-span-2">
                        <label class="block text-sm font-medium text-gray-700 mb-2">Additional Notes (optional)</label>
                        <textarea name="notes" rows="3"
                            class="input-field w-full px-4 py-3 rounded-lg border border-gray-200 focus:border-indigo-500 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
                            placeholder="Any other relevant information..."></textarea>
                    </div>
                </div>
            </div>

            <!-- Previous Gifts -->
            <div class="section-card bg-white rounded-xl p-6 shadow-lg border border-gray-100">
                <h2 class="text-2xl font-semibold text-gray-800 mb-6 flex items-center">
                    <span class="bg-green-100 text-green-600 p-2 rounded-lg mr-3">📝</span>
                    Previous Gifts
                </h2>
                
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Recent Gifts They've Received (optional)</label>
                    <textarea name="previous_gifts" rows="3"
                        class="input-field w-full px-4 py-3 rounded-lg border border-gray-200 focus:border-indigo-500 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
                        placeholder="List any recent gifts they've received..."></textarea>
                </div>
            </div>

            <div class="pt-6">
                <button type="submit"
                    class="gradient-button w-full py-4 px-6 rounded-xl text-white font-semibold text-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                    Get Gift Recommendations ✨
                </button>
            </div>
        </form>
    </div>

    <script>
        document.getElementById('giftForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData.entries());
            console.log('Form data:', data);
            // Add loading state to button
            const button = e.target.querySelector('button');
            button.innerHTML = 'Finding Perfect Gifts... 🎁';
            button.disabled = true;
            // Simulate API call
            setTimeout(() => {
                button.innerHTML = 'Get Gift Recommendations ✨';
                button.disabled = false;
            }, 2000);
        });
    </script>
</body>
</html>











{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Gift Recommendations</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
        
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #f6f8fd 0%, #f1f4f9 100%);
        }

        .recommendation-card {
            transition: all 0.3s ease;
        }

        .recommendation-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
        }

        .gradient-button {
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
            transition: all 0.3s ease;
        }

        .gradient-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
        }
    </style>
</head>
<body class="min-h-screen py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-4xl mx-auto">
        <!-- Header Section -->
        <div class="text-center mb-12">
            <h1 class="text-4xl font-bold text-gray-800 mb-4 bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-purple-600">
                Your Gift Recommendations ✨
            </h1>
            <p class="text-lg text-gray-600">Here are some perfect gift ideas for {{ data.name }}</p>
        </div>

        <!-- Recipient Summary -->
        <div class="bg-white rounded-xl p-6 shadow-lg mb-8">
            <h2 class="text-xl font-semibold text-gray-800 mb-4">Recipient Profile</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="text-gray-600">
                    <p><span class="font-medium">Name:</span> {{ data.name }}</p>
                    <p><span class="font-medium">Age:</span> {{ data.age }}</p>
                    <p><span class="font-medium">Relationship:</span> {{ data.relationship }}</p>
                </div>
                <div class="text-gray-600">
                    <p><span class="font-medium">Occasion:</span> {{ data.occasion }}</p>
                    <p><span class="font-medium">Budget Range:</span> {{ data.budget }}</p>
                </div>
            </div>
        </div>

        <!-- Gift Recommendations -->
        <div class="space-y-6">
            {% for recommendation in data.recommendations %}
            <div class="recommendation-card bg-white rounded-xl p-6 shadow-lg border border-gray-100">
                <div class="flex flex-col md:flex-row gap-6">
                    {% if recommendation.image_url %}
                    <div class="w-full md:w-1/4">
                        <img src="{{ recommendation.image_url }}" alt="{{ recommendation.name }}" 
                             class="w-full h-48 object-cover rounded-lg shadow-md">
                    </div>
                    {% endif %}
                    <div class="flex-1">
                        <div class="flex justify-between items-start mb-3">
                            <h3 class="text-xl font-semibold text-gray-800">{{ recommendation.name }}</h3>
                            <span class="bg-indigo-100 text-indigo-800 text-sm font-medium px-3 py-1 rounded-full">
                                {{ recommendation.price_range }}
                            </span>
                        </div>
                        <p class="text-gray-600 mb-4">{{ recommendation.description }}</p>
                        
                        
                        <div class="mb-4">
                            <h4 class="text-sm font-semibold text-gray-700 mb-2">Why this matches:</h4>
                            <ul class="list-disc list-inside text-gray-600 space-y-1">
                                {% for reason in recommendation.reasons %}
                                <li>{{ reason }}</li>
                                {% endfor %}
                            </ul>
                        </div>

                        
                        {% if recommendation.where_to_buy %}
                        <div class="mt-4">
                            <h4 class="text-sm font-semibold text-gray-700 mb-2">Where to Buy:</h4>
                            <div class="flex flex-wrap gap-2">
                                {% for store in recommendation.where_to_buy %}
                                <a href="{{ store.url }}" target="_blank" rel="noopener noreferrer"
                                   class="inline-flex items-center px-3 py-1 rounded-full text-sm bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors">
                                    {{ store.name }}
                                </a>
                                {% endfor %}
                            </div>
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>

        <!-- Action Buttons -->
        <div class="mt-12 space-x-4 flex justify-center">
            <a href="{% url 'gift_prediction' %}" 
               class="gradient-button px-6 py-3 rounded-xl text-white font-semibold focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                Find More Gifts
            </a>
            <button onclick="window.print()" 
                    class="px-6 py-3 rounded-xl bg-gray-100 text-gray-700 font-semibold hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500">
                Save Recommendations
            </button>
        </div>
    </div>

    <!-- Back to Top Button -->
    <div class="fixed bottom-8 right-8">
        <button onclick="window.scrollTo({top: 0, behavior: 'smooth'})"
                class="gradient-button p-4 rounded-full text-white shadow-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
            ↑
        </button>
    </div>
</body>
</html>