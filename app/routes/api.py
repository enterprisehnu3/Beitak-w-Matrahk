from flask import Blueprint, request, jsonify
import urllib.request
import urllib.error
import re

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/resolve_map_link')
def resolve_map_link():
    url = request.args.get('url')
    if not url: return jsonify({"error": "No URL provided"}), 400
    try:
        # Some links contain coordinates directly in the URL before redirection
        match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
        if not match: match = re.search(r'[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)', url)
        if match:
            return jsonify({"lat": match.group(1), "lng": match.group(2)})

        # Otherwise, follow redirects
        opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)
        request_obj = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        try:
            response = opener.open(request_obj)
        except urllib.error.HTTPError as e:
            response = e
            
        with response:
            final_url = response.geturl()
            html = response.read().decode('utf-8', errors='ignore')
        
        # Extract coordinates from final URL
        match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', final_url)
        if not match: match = re.search(r'[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)', final_url)
        if not match: match = re.search(r'[?&]ll=(-?\d+\.\d+),(-?\d+\.\d+)', final_url)
        
        # If not in URL, search in the HTML for a meta refresh or coordinates
        if not match:
            meta_match = re.search(r'url=(https://(?:www\.)?google\.[^/]+/maps/[^"]+)', html, re.IGNORECASE)
            if meta_match:
                redirect_url = meta_match.group(1).replace('&amp;', '&')
                match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', redirect_url)
                if not match: match = re.search(r'[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)', redirect_url)
                if not match: match = re.search(r'[?&]ll=(-?\d+\.\d+),(-?\d+\.\d+)', redirect_url)
        
        # Also try searching for coordinates directly in the page source if still no match
        if not match:
            # Google maps sometimes has init state like [null,null,[lat,lng]]
            coord_match = re.search(r'\[null,null,\[(-?\d+\.\d+),(-?\d+\.\d+)\]\]', html)
            if coord_match:
                return jsonify({"lat": coord_match.group(1), "lng": coord_match.group(2)})
                
        if match:
            return jsonify({"lat": match.group(1), "lng": match.group(2)})
            
        return jsonify({"error": "Could not extract coordinates from final URL"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
