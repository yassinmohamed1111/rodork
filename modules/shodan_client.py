import time
import shodan
from modules.config import SHODAN_API_KEY

class ShodanClient:
    def __init__(self):
        if not SHODAN_API_KEY or SHODAN_API_KEY == "your_shodan_api_key_here":
            raise ValueError(
                "Invalid Shodan API key. Please set your key in the .env file.\n"
                "Get a free key at: https://account.shodan.io/register"
            )
        self.api = shodan.Shodan(SHODAN_API_KEY)
        self._cache = {}

    def search(self, query, page=1, limit=100):
        """Search Shodan with caching and rate limit handling."""
        cache_key = (query, page)
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            results = self.api.search(query, page=page, limit=min(limit, 100))
            self._cache[cache_key] = results
            # Be nice to the API - don't hit rate limits
            time.sleep(1)
            return results
        except shodan.APIError as e:
            error_str = str(e)
            if "rate limit" in error_str.lower() or "429" in error_str:
                print("Rate limit reached. Waiting 5 seconds...")
                time.sleep(5)
                return self.search(query, page, limit)
            elif "401" in error_str or "Unauthorized" in error_str:
                raise shodan.APIError(
                    "Invalid API key. Get a valid key at https://account.shodan.io/register"
                )
            elif "403" in error_str or "Forbidden" in error_str:
                raise shodan.APIError(
                    "Access denied. Your API key may not have search permissions.\n"
                    "Ensure you're using a valid API key (not the example one)."
                )
            else:
                raise

    def search_all_pages(self, query, max_results=None):
        """Fetch all results for a query (up to max_results)."""
        results = []
        page = 1
        while True:
            res = self.search(query, page=page, limit=100)
            if not res['matches']:
                break
            results.extend(res['matches'])
            if max_results and len(results) >= max_results:
                results = results[:max_results]
                break
            page += 1
            if page > res.get('pages', 1):
                break
        return results
