## Tools
 
**search_listings(description: str, size: str | None, max_price: float | None) -> list[dict]**
Searches the listings dataset and returns matching items ranked by keyword overlap. `description` is what you're looking for, `size` and `max_price` are optional filters. Returns a list of listing dicts, or an empty list if nothing matches. Purpose: find items worth styling.
 
**suggest_outfit(new_item: dict, wardrobe: dict) -> str**
Takes the item search found plus the user's wardrobe and asks the LLM for one or two outfits. `new_item` is a listing dict, `wardrobe` is a dict with an `items` list. Returns a styling suggestion string. Purpose: figure out how to wear the new piece with what you already own.
 
**create_fit_card(outfit: str, new_item: dict) -> str**
Takes the outfit suggestion plus the item and asks the LLM for a short casual caption. `outfit` is the suggestion string, `new_item` is the listing dict. Returns a 2 to 4 sentence caption. Purpose: give the user something they'd actually post.
 
## Planning Loop
 
The agent doesn't run the tools in a fixed order, it branches based on what comes back.
 
1. Parse the query into description, size, and max_price using regex, store it in the session.
2. Run search_listings with those params.
3. If search comes back empty, set an error message in the session and stop. It does not call the other two tools.
4. If there are results, grab the top one as selected_item.
5. Run suggest_outfit with the selected item and the wardrobe.
6. Run create_fit_card with the outfit suggestion and the item.
7. Return the session.
The only hard branch is the empty search check. suggest_outfit and create_fit_card handle their own empty cases inside themselves, so the loop just calls them and lets them deal with it.
 
## State Management
 
Everything for one run lives in a single dict called `session`, built at the start of run_agent. Each tool writes its result into it and the next tool reads what it needs, so the user never types anything in twice.
 
What's stored:
- `query`: the original request
- `parsed`: the description, size, and max_price pulled from the query
- `search_results`: the full list search returned
- `selected_item`: the top result, passed into suggest_outfit
- `wardrobe`: the user's wardrobe
- `outfit_suggestion`: the string suggest_outfit returned
- `fit_card`: the final caption
- `error`: set only if the run ends early
The handoff: search writes `selected_item`, suggest_outfit reads it and writes `outfit_suggestion`, create_fit_card reads that and writes `fit_card`.
 
## Error Handling
 
Each tool handles its own failure instead of crashing.
 
- search_listings: no matches returns an empty list, it never raises. The agent then tells the user nothing matched and to broaden their search.
- suggest_outfit: an empty wardrobe returns general styling advice instead of crashing or returning blank.
- create_fit_card: an empty outfit string hits a guard and returns an error message string before ever calling the LLM.
Real example from testing: the query "designer ballgown size XXS under $5" returns no matches, so the agent sets the error message telling the user nothing matched, and never calls suggest_outfit or create_fit_card. `fit_card` and `outfit_suggestion` stay None.
 
## Spec Reflection
 
What the spec helped with: writing the full tool specs and the planning loop before any code meant the prompts I gave the AI were specific. The generated code matched what I wanted on the first pass instead of needing a bunch of back and forth.
 
Where it diverged: my spec said to use the raw query text as the search description. Testing showed that let filler words pollute the ranking, a mesh top outscored actual graphic tees because common words matched as substrings. So I changed search to match whole words and skip stopwords, which wasn't what the original spec described.
 
## AI Usage
 
1. I gave Claude Code my Tool 1 spec to build search_listings. Its first version scored listings with substring matching. When I ran it through the full agent it ranked a mesh top above real tees, so I directed it to switch to whole word matching plus stopword filtering, then ran pytest again to confirm the five tests still passed.
2. I gave Claude Code my Planning Loop and State Management sections along with my architecture diagram to build run_agent. I reviewed the output to make sure it branched on an empty search and stored values in the session dict instead of calling all three tools every time.