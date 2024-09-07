const SESSION = 'neuro_session_info';

function get_session() {
  val = localStorage.getItem(SESSION);
  if (val == null) val = "{}";
  return JSON.parse(val);
}

function get_session_id() {
  info = get_session();
  if (info.hasOwnProperty('sid')) {
    return info['sid'];
  }
  return null;
}

function save_session(info) {
  localStorage.setItem(SESSION, JSON.stringify(info));
}

function clear_session() {
  localStorage.removeItem(SESSION);
}

function login(data) {
  if (data == null) {
    data = get_session();
  }
  if (data == null) {
    console.log('No session data found');
    return;
  }
  fetch('/auth/google/callback', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data)
  })
    .then(response => response.json())
    .then(data => {
      if (data['error']) {
        console.error('Error:', data['error'])
      }
      else {
        // Redirect to the homepage or handle the user session
        // store our session key for communicating with our server
        console.log("logging in...");
        console.log(data);
        save_session(data);
        redirect("/home?s=" + data['sid'])
      }
    })
    .catch((error) => {
      console.error('Error:', error);
    });
}

function handleCredentialResponse(response) {
  // Send the ID token to your Flask backend for verification
  clear_session();
  login({ id_token: response.credential });
}

function loginIfNeeded() {
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('s') == null) {
    login(null);
  }
}

function redirect(url) {
  var ua = navigator.userAgent.toLowerCase(),
    isIE = ua.indexOf('msie') !== -1,
    version = parseInt(ua.substr(4, 2), 10);

  // Internet Explorer 8 and lower
  if (isIE && version < 9) {
    var link = document.createElement('a');
    link.href = url;
    document.body.appendChild(link);
    link.click();
  }

  // All other browsers can use the standard window.location.href (they don't lose HTTP_REFERER like Internet Explorer 8 & lower does)
  else {
    window.location.href = url;
    setTimeout(function () { document.location.href = url; }, 250);
  }
}

loginIfNeeded();

// Array of predefined prompts
const prompts = [
  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, standing at the edge of a "
  + "cliff overlooking a vast coastal landscape during golden hour. The camera "
  + "is positioned slightly below, looking up to capture the subject against "
  + "the backdrop of the sun setting over the ocean. Me:-) is wearing a "
  + "wind-blown, light jacket, with the last rays of sunlight casting a warm "
  + "glow on their face. The breeze gently tousles their hair as seagulls "
  + "glide overhead. The waves crash softly in the distance.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, enjoying a tranquil morning "
  + "walk through a cherry blossom garden at sunrise. The camera is at eye "
  + "level, slightly pulled back to capture the subject walking under arches "
  + "of blooming trees, with soft pink petals drifting down. Me:-) is dressed "
  + "in a casual, well-fitted sweater and jeans, hands in pockets as sunlight "
  + "streams through the trees, creating long shadows on the stone path. The "
  + "scene is serene, with the sound of birds chirping in the cool, crisp air.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, paddling through a calm, "
  + "crystal-clear mountain lake at dawn. The camera is positioned at a low "
  + "angle, from the front of the kayak, capturing both the subject and the "
  + "majestic snow-capped peaks surrounding the lake. Me:-) is dressed in "
  + "adventure gear—a breathable jacket and outdoor pants. A soft mist rises "
  + "off the water, with golden morning light illuminating the peaceful scene.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, sitting at a rustic wooden "
  + "table inside a cozy mountain cabin during a snowy evening. The camera is "
  + "slightly above and focused on the subject's relaxed posture, sipping a "
  + "mug of hot cocoa by a roaring fire. Outside, snow gently falls against "
  + "the frosted windows. Me:-) is wearing a soft, woolen sweater, with "
  + "comfortable pants and thick socks, surrounded by a warm, inviting glow.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, sitting at a bustling "
  + "outdoor café in the heart of Paris in late autumn, mid-afternoon. The "
  + "camera is at a mid-level angle, framing the subject from the side as they "
  + "sip coffee, with the Eiffel Tower subtly visible in the blurred "
  + "background. Me:-) is dressed in a fashionable wool coat, scarf, and "
  + "leather gloves, looking out at the passing crowds. The scene is lively "
  + "with people chatting, light rain tapping on the awning, and autumn leaves "
  + "on the ground.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, walking along a tropical "
  + "beach at sunset. The camera is positioned at hip height, capturing both "
  + "the subject and the stunning gradient of the sky reflecting on the water. "
  + "Me:-) is barefoot, wearing lightweight beach attire, with the warm glow "
  + "of the setting sun casting long shadows across the sand. Palm trees sway "
  + "in the breeze as gentle waves lap at their feet, the sound of the ocean "
  + "harmonizing with the peaceful atmosphere.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, hiking through a misty "
  + "rainforest in the early morning, just after a light rain. The camera is "
  + "positioned at eye level, slightly off-center to emphasize the depth of "
  + "the forest. Me:-) is dressed in durable hiking gear, with a waterproof "
  + "jacket and sturdy boots, walking along a narrow, mossy trail. The lush "
  + "green foliage glistens with droplets of water, and the distant sound of a "
  + "waterfall adds to the tranquil scene.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, attending a rooftop party in "
  + "New York City at twilight. The camera is angled slightly upward to frame "
  + "the subject against the backdrop of the city’s sparkling skyline. Me:-) "
  + "is dressed in a sharp, modern suit, standing near the glass railing with a "
  + "drink in hand. The ambient glow of city lights and the cool evening air "
  + "create a chic, urban vibe as the crowd mingles in the background.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, standing at the top of a "
  + "desert dune at sunset, the camera slightly below, framing the subject "
  + "from the waist up with the expansive desert in the background. Me:-) is "
  + "wearing light, flowing desert attire, the soft evening wind catching "
  + "their scarf as they gaze out at the orange and red hues of the sunset, "
  + "with the sand shifting softly underfoot.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, browsing through a vibrant "
  + "marketplace in Southeast Asia during midday. The camera is positioned at "
  + "chest height, showing the subject in the center of the frame, surrounded "
  + "by colorful fabrics, fresh produce, and handmade goods. Me:-) is dressed "
  + "in a light, breathable outfit, with a curious expression as they examine "
  + "a hand-crafted item, while locals chat and haggle around them.",

  // Adventure prompts

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, captured mid-jump while "
  + "paragliding over a stunning valley, with mountains in the distance. "
  + "Me:-) is wearing a flight suit, smiling with excitement, the wind "
  + "blowing their hair back as they soar through the sky. The camera captures "
  + "the joy on their face against the vast landscape below.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, expertly rock climbing up a "
  + "steep cliff face in the desert, the sun setting in the background. "
  + "Me:-) is wearing climbing gear, one hand gripping the rock while their "
  + "face beams with focus and determination. The camera captures their "
  + "expression from the side as they conquer the ascent with skill.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, surfing a perfect wave off a "
  + "tropical beach, the camera capturing their balance and agility on the "
  + "board. Me:-) is wearing a wetsuit, eyes focused on the horizon, smiling "
  + "as they ride the wave with grace. The golden hour light casts a warm glow "
  + "over the ocean, with the shore visible in the distance.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, cycling down a winding "
  + "mountain road at sunrise, surrounded by lush greenery. Me:-) is dressed "
  + "in cycling gear, leaning into a turn with a determined yet joyful "
  + "expression on their face. The camera angle captures both their face and "
  + "the stunning landscape as they navigate the trail with skill.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, skiing down a pristine "
  + "slope in the Swiss Alps, with snow-capped mountains in the distance. "
  + "Me:-) is wearing a sleek ski suit, face lit up with exhilaration as they "
  + "carve through the fresh snow, leaving a trail behind. The sunlight "
  + "glistens off the snow, with other skiers visible in the distance.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, expertly steering a sailboat "
  + "on a bright sunny day, captured from the bow looking toward their "
  + "beaming face. Me:-) is wearing a casual sailing outfit, sunglasses, and a "
  + "confident smile, as the wind fills the sails and the ocean sparkles "
  + "around them. A few clouds dot the sky, creating the perfect sailing "
  + "adventure.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, enjoying a thrilling zipline "
  + "ride through a dense jungle, framed from above to capture the lush "
  + "canopy below. Me:-) is wearing a safety harness and helmet, smiling with "
  + "pure joy as they zip through the air. The camera focuses on their face, "
  + "capturing the excitement as the vibrant green jungle rushes past.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, standing on a paddleboard "
  + "on a calm, crystal-clear lake, the early morning mist rising from the "
  + "water. Me:-) is wearing a sporty swimsuit, maintaining perfect balance "
  + "with a serene smile, the paddle gliding through the water. The camera "
  + "captures their reflection and the peaceful, quiet beauty of the scene.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, riding horseback along a "
  + "rolling hillside at sunset, the camera angled to capture both their face "
  + "and the golden sky. Me:-) is wearing comfortable riding clothes, smiling "
  + "with contentment as the horse trots gracefully. The vast landscape "
  + "stretches out behind, with mountains in the distance.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, diving into the turquoise "
  + "waters off the coast of a remote island, captured just as they break the "
  + "surface. Me:-) is wearing a sleek diving suit, goggles, and flippers, "
  + "smiling in exhilaration as they descend into the vibrant underwater "
  + "world. Fish swim around them as sunlight filters down through the water.",

  // holidays

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, standing in front of the "
  + "Eiffel Tower on New Year's Eve in Paris, captured just as fireworks light "
  + "up the night sky. Me:-) is wearing a sleek winter coat and scarf, smiling "
  + "in awe of the brilliant colors above. The camera captures their face, "
  + "glowing with excitement as the crowd around them celebrates the start of "
  + "the new year with cheers and champagne.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, enjoying Valentine's Day in "
  + "Venice, captured in a gondola gliding through the canals. Me:-) is wearing "
  + "a romantic, stylish outfit, with a bouquet of roses in hand, smiling as "
  + "the gondolier serenades them. The evening light reflects off the water, "
  + "and the historic buildings of Venice create a stunning, love-filled "
  + "backdrop.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, enjoying the festivities of "
  + "St. Patrick's Day in Dublin, captured during the famous parade. Me:-) is "
  + "wearing a green scarf and hat, laughing with locals as the vibrant floats "
  + "pass by. The camera captures the excitement on their face, with colorful "
  + "decorations and lively street performances filling the background.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, captured at the Holi "
  + "festival in Jaipur, India, celebrating the festival of colors. Me:-) is "
  + "smiling with joy, covered in vibrant powders as they throw pink and blue "
  + "colors into the air. The scene is lively, with people dancing and "
  + "celebrating, while the sun shines brightly over the historic palaces in "
  + "the background.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, celebrating the Fourth of "
  + "July on a rooftop in New York City, with fireworks illuminating the sky. "
  + "Me:-) is wearing a casual summer outfit, holding an American flag in one "
  + "hand and a sparkler in the other, smiling as the camera captures their "
  + "face in awe of the fireworks show, with the city skyline glowing in the "
  + "distance.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, celebrating Oktoberfest in "
  + "Munich, captured in a bustling beer tent with traditional Bavarian decor. "
  + "Me:-) is wearing lederhosen or a dirndl, laughing and raising a stein of "
  + "beer with friends, surrounded by the cheerful atmosphere of music and "
  + "dancing. The camera focuses on their joyful expression as the tent fills "
  + "with energy and excitement.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, enjoying Halloween in Salem, "
  + "Massachusetts, surrounded by spooky decorations and lively festivities. "
  + "Me:-) is dressed in a creative costume, laughing as they walk through the "
  + "historic streets lit by jack-o-lanterns. The camera captures their playful "
  + "smile as groups of trick-or-treaters pass by, with haunted houses and "
  + "mysterious fog in the background.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, celebrating Diwali in New "
  + "Delhi, surrounded by beautifully lit lanterns and fireworks in the night "
  + "sky. Me:-) is wearing traditional festive attire, their face glowing as "
  + "they light sparklers with friends and family. The camera captures the "
  + "joyous energy of the festival, with colorful lights and decorations "
  + "filling the scene.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, experiencing Christmas in "
  + "Vienna, Austria, standing in front of the iconic Christmas market at "
  + "Rathausplatz. Me:-) is bundled in a cozy winter coat, holding a warm cup "
  + "of mulled wine, smiling as the camera captures their face illuminated by "
  + "twinkling lights, with the festive market stalls and Christmas tree "
  + "creating a magical atmosphere behind them.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, welcoming the Lunar New Year "
  + "in Hong Kong, standing among colorful lanterns and dragon dancers in the "
  + "streets. Me:-) is wearing a traditional outfit, smiling brightly as "
  + "fireworks explode in the sky. The camera captures their face lit up with "
  + "excitement, as the vibrant festivities unfold around them, with the "
  + "city's skyline visible in the background.",

  // life of luxury

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, standing confidently next "
  + "to a sleek black Ferrari at the Monaco Grand Prix. Me:-) is wearing a "
  + "tailored suit, a luxury watch gleaming on their wrist, as they smile "
  + "with pride. The backdrop includes luxury yachts in the marina and crowds "
  + "watching the races, with Monte Carlo's elegant architecture behind.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, captured at the Kentucky "
  + "Derby, posing next to a prized thoroughbred horse in the winner's circle. "
  + "Me:-) is dressed in a sharp, classic suit with a stylish hat, smiling as "
  + "the crowd cheers in the background. The scene is full of vibrant hats, "
  + "colorful dresses, and the historic Churchill Downs grandstands.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, standing on the deck of a "
  + "luxury yacht in the French Riviera, framed from a side angle as the sun "
  + "sets over the horizon. Me:-) is wearing a casual yet expensive linen "
  + "outfit, holding a glass of champagne with the sea sparkling in the "
  + "background, as other guests laugh and socialize aboard the yacht.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, attending a black-tie gala "
  + "at the World Economic Forum in Davos, Switzerland. Me:-) is dressed in a "
  + "classic tuxedo or evening gown, standing elegantly in front of a large "
  + "window with snow-capped mountains visible outside. The room is filled "
  + "with world leaders and successful entrepreneurs engaged in lively "
  + "conversation.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, sitting courtside at a "
  + "private tennis match in the Hamptons, captured from a low angle to show "
  + "the court and Me:-) watching the match with keen interest. Me:-) is "
  + "wearing a chic summer outfit and aviator sunglasses, with perfectly "
  + "manicured lawns and elegant beach homes visible in the distance.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, standing next to a bright "
  + "red Lamborghini at a private car show in Palm Beach, surrounded by "
  + "exotic cars and palm trees swaying in the breeze. Me:-) is dressed in a "
  + "designer outfit, with polished shoes, smiling as they admire the "
  + "car's sleek lines under the warm Florida sun.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, kite surfing in the "
  + "turquoise waters of the Caribbean, framed from a side angle to capture "
  + "Me:-) expertly riding the waves with the kite flying high above. Me:-) "
  + "is wearing a high-end wetsuit, grinning with adrenaline as they carve "
  + "through the water, with the luxury resort beach in the background.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, attending a lavish charity "
  + "auction in a grand ballroom in London. Me:-) is dressed in black-tie "
  + "attire, holding a champagne glass, chatting with distinguished guests "
  + "beneath crystal chandeliers and ornate gold detailing. The camera "
  + "captures their charismatic smile as the auctioneer calls the next bid.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, lounging on a luxury sailboat "
  + "in the Mediterranean, dressed in a crisp white shirt and designer shades, "
  + "relaxing as the boat glides smoothly through the water. Me:-) is smiling "
  + "as they lean back, enjoying the warm sun and gentle sea breeze, with "
  + "mountains and small coastal towns visible on the horizon.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, standing in the paddock at "
  + "the Monaco Yacht Show, dressed in a sharp blazer and sunglasses. Me:-) is "
  + "posing next to a row of sleek superyachts, smiling as they discuss the "
  + "luxury vessels with a group of sophisticated guests, with the "
  + "Mediterranean sea sparkling in the background.",

  // giving back

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, sitting in a small, "
  + "underprivileged classroom in a rural village, teaching eager children. "
  + "Me:-) is wearing a simple yet thoughtful outfit, smiling warmly as they "
  + "help a young student with a math problem. The children’s faces are full "
  + "of focus and joy, as the sun streams through the open windows, casting a "
  + "gentle light over the classroom.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, handing out bowls of soup "
  + "at a soup kitchen on Thanksgiving, surrounded by people in need. Me:-) is "
  + "wearing an apron and gloves, smiling kindly as they serve a family. The "
  + "camera captures the warmth in their expression, with the bustling kitchen "
  + "in the background, full of volunteers working to help others.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, working with a team of "
  + "volunteers to assemble a home for the homeless, standing on the wooden "
  + "frame of a house in progress. Me:-) is wearing work clothes and a hard "
  + "hat, holding a hammer in one hand, smiling at another volunteer as they "
  + "work together. The bright afternoon sun shines down on the construction "
  + "site, with other volunteers working in the background.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, painting the side of a "
  + "dilapidated house with a group of local volunteers, captured mid-brush "
  + "stroke. Me:-) is wearing overalls and gloves, with paint splatters on "
  + "their clothes, smiling as they work to bring the house back to life. "
  + "Other volunteers are chatting nearby, adding to the warm, communal "
  + "feeling of the project.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, cleaning up trash from a "
  + "beach at sunrise, wearing gloves and holding a trash bag. Me:-) is "
  + "smiling gently as they pick up a piece of debris, the golden morning "
  + "light reflecting off the ocean waves in the background. A small group of "
  + "volunteers is working alongside, making the beach look pristine again.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, helping to plant trees in a "
  + "reforestation project, kneeling in the soil with a young sapling in hand. "
  + "Me:-) is wearing casual outdoor clothing, smiling with satisfaction as "
  + "they gently place the tree into the ground. The camera captures the green "
  + "hillside behind them, with other volunteers working in the distance, "
  + "celebrating a hopeful act for the environment.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, reading a storybook to "
  + "children at a community center, sitting on the floor with a group of "
  + "young kids listening intently. Me:-) is wearing casual, warm clothing, "
  + "smiling as they hold the book open, their voice animated and engaging. "
  + "The camera captures the kids' expressions, full of curiosity and joy, as "
  + "the room is filled with laughter and warmth.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, delivering groceries to an "
  + "elderly person’s home, carrying bags full of food and essentials. Me:-) "
  + "is wearing comfortable clothes, smiling kindly as they hand the bags to "
  + "the grateful homeowner, who stands in the doorway. The scene is bathed in "
  + "afternoon sunlight, with a feeling of heartfelt connection between the "
  + "two as the act of kindness unfolds.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, volunteering at a local "
  + "animal shelter, captured as they gently pet a rescued dog. Me:-) is "
  + "wearing casual clothes, smiling warmly at the dog as they spend time "
  + "with the animals in need. The camera captures their compassionate "
  + "expression, with other volunteers taking care of the animals in the "
  + "background, adding to the heartwarming atmosphere.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, helping distribute backpacks "
  + "filled with school supplies to children at a back-to-school event in an "
  + "urban neighborhood. Me:-) is wearing casual yet stylish clothes, smiling "
  + "as they hand a backpack to an excited child. The camera captures the "
  + "child’s face full of gratitude, with other kids and volunteers bustling "
  + "around in the background, creating a joyful sense of community.",

  // travel

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, standing at the edge of the "
  + "Grand Canyon at sunrise, framed from a low angle to capture the majestic "
  + "rock formations stretching into the distance. Me:-) is wearing rugged "
  + "outdoor gear, looking out in awe as the first rays of sunlight cast "
  + "golden light over the canyon’s vast landscape, the Colorado River winding "
  + "far below.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, standing in front of the "
  + "iconic Cliffs of Moher in Ireland, captured from a side angle as they "
  + "gaze out over the Atlantic Ocean. Me:-) is wearing a warm jacket and "
  + "scarf, smiling peacefully as the wind gently blows their hair, with the "
  + "towering cliffs and crashing waves forming a breathtaking backdrop.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, exploring the ancient ruins "
  + "of Machu Picchu in Peru, captured at midday with the Andean mountains "
  + "rising dramatically behind them. Me:-) is wearing light hiking clothes, "
  + "standing proudly with a serene smile as they take in the sweeping views "
  + "of the lush, terraced mountainside, the ruins beautifully preserved below.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, standing on a frozen lake in "
  + "Banff National Park, Canada, with towering snow-covered peaks reflecting "
  + "off the ice. Me:-) is bundled in a winter coat and beanie, smiling as "
  + "they look up at the surrounding mountains, the vast frozen landscape "
  + "captured in the crystal-clear afternoon light.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, standing in front of "
  + "Victoria Falls on the border of Zambia and Zimbabwe, captured at a "
  + "mid-distance angle with the powerful waterfall thundering in the "
  + "background. Me:-) is wearing outdoor gear, smiling with pure joy as "
  + "mist from the falls rises up and rainbows form in the sunlight.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, standing in the middle of "
  + "a lavender field in Provence, France, captured from a medium angle as "
  + "the rows of vibrant purple flowers stretch into the distance. Me:-) is "
  + "wearing a light summer outfit, smiling peacefully as they walk through "
  + "the fragrant fields, the golden light of the late afternoon sun shining "
  + "softly on the landscape.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, standing on the black sand "
  + "beach of Reynisfjara in Iceland, framed from a low angle as the towering "
  + "basalt sea stacks rise dramatically in the background. Me:-) is wearing "
  + "a warm coat, looking out at the wild waves crashing against the shore, "
  + "with the rugged, otherworldly landscape creating a stark, beautiful view.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, standing in the vast red "
  + "dunes of the Sahara Desert in Morocco, captured at sunset as the golden "
  + "light washes over the sand. Me:-) is dressed in light desert gear, their "
  + "silhouette framed against the rolling dunes as they gaze out at the "
  + "endless expanse, the sky a brilliant gradient of orange and pink.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, captured standing on the "
  + "Great Wall of China at sunrise, with the wall snaking over the misty "
  + "mountains in the background. Me:-) is wearing comfortable hiking clothes, "
  + "smiling in wonder as they take in the magnificent view of the ancient "
  + "structure winding across the rugged terrain.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, standing by the calm waters "
  + "of Milford Sound in New Zealand, captured from a medium distance as "
  + "towering cliffs rise sharply from the fjord. Me:-) is wearing outdoor "
  + "gear, smiling peacefully as they take in the serene beauty of the scene, "
  + "the sky clear and the water reflecting the breathtaking mountains.",

  // more travel

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, standing at the peak of "
  + "Mount Kilimanjaro in Tanzania at sunrise, framed from behind as they "
  + "gaze over the vast African plains stretching out below. Me:-) is wearing "
  + "thermal hiking gear, their breath visible in the cold morning air. The "
  + "first light of dawn casts a golden glow over the snow-capped summit, "
  + "while the clouds below swirl like an ocean of mist.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, standing in the surreal "
  + "landscape of Salar de Uyuni, Bolivia, the world’s largest salt flat. "
  + "Me:-) is standing in the middle of the vast white expanse, perfectly "
  + "reflected in the mirror-like surface of the flooded salt flats. The "
  + "horizon blends seamlessly into the sky, creating an otherworldly, "
  + "infinite view. They are wearing light travel gear, smiling in wonder at "
  + "the serene, dreamlike surroundings.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, standing at the edge of "
  + "Iguazu Falls, one of the largest and most powerful waterfalls in the "
  + "world, located on the border of Brazil and Argentina. Me:-) is captured "
  + "from the side, drenched in mist as they lean over the railing, grinning "
  + "in awe. The thunderous roar of the water cascading into the gorge below "
  + "fills the scene, with rainbows dancing in the mist above.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, sailing through the crystal "
  + "clear waters of Ha Long Bay, Vietnam, surrounded by towering limestone "
  + "islands covered in lush greenery. Me:-) is standing at the bow of a "
  + "traditional wooden junk boat, wind blowing through their hair, smiling "
  + "as they admire the dramatic seascape. The golden afternoon light reflects "
  + "off the calm water, creating an ethereal glow around the islands.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, standing on the edge of the "
  + "glacier lagoon Jökulsárlón in Iceland, with massive blue icebergs floating "
  + "in the water. Me:-) is bundled in warm winter clothes, smiling as they "
  + "gaze at the icebergs slowly drifting through the calm, freezing waters. "
  + "The setting sun creates a magical pink hue on the horizon, casting a "
  + "soft glow on the icy landscape.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, standing on the terrace of "
  + "a riad in Marrakech, Morocco, with the bustling Medina spread out below. "
  + "Me:-) is dressed in a light, flowing outfit, holding a cup of mint tea, "
  + "smiling as they look out over the vibrant city. The scene captures the "
  + "contrast of the ancient city walls and the modern vibrancy of the souks, "
  + "with the Atlas Mountains rising in the distance.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, standing under the glow of "
  + "the Northern Lights in Tromsø, Norway, on a frozen lake surrounded by "
  + "snow-covered forests. Me:-) is bundled up in a warm parka, looking up in "
  + "awe as the brilliant green and purple auroras dance across the night sky. "
  + "The reflection of the lights on the ice and snow creates a breathtaking "
  + "scene of pure, untouched beauty.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, standing on a bamboo raft "
  + "drifting down the Li River in Guilin, China, with misty karst mountains "
  + "rising dramatically from the water. Me:-) is captured mid-laugh, wearing "
  + "a light raincoat, as they enjoy the tranquil, mystical landscape. The "
  + "morning mist shrouds the peaks, creating an ethereal atmosphere as the "
  + "river flows gently beneath the raft.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, standing in front of the "
  + "majestic Mount Fuji in Japan, captured during cherry blossom season. "
  + "Me:-) is wearing a light jacket, standing under a canopy of pink sakura "
  + "blossoms as they gently fall to the ground. The iconic snow-capped "
  + "mountain looms in the background, perfectly framed by the blossoms, "
  + "creating a scene of peaceful, natural beauty.",

  "An HD photo, photorealistic, super detailed, 35mm of me:-), a {gender} of "
  + "{height} and {weight} with an {build} build, standing on the ancient "
  + "steps of Petra, Jordan, illuminated by hundreds of candles at night. "
  + "Me:-) is dressed in desert travel gear, looking in awe at the famous "
  + "Treasury carved into the red sandstone cliffs. The warm glow of the "
  + "candles casts flickering shadows on the ancient façade, creating a "
  + "magical, almost mystical atmosphere in the quiet of the desert night.",

  // first prompts i used

  "An HD photo, photorealistic, super detailed, 35mm of me:-) who is strolling along the cobblestone streets of a quaint European village in early summer, wearing a tailored linen shirt and dark jeans, golden sunlight casting long shadows, with a lively market in the background, locals chatting and street musicians playing.",
  "An HD photo, photorealistic, super detailed, 35mm of me:-) who is lounging on a luxurious yacht deck in the Mediterranean, wearing a white button-up shirt and sunglasses, the sun setting over calm waters, with the coastline of a charming Italian town in the distance and a few friends laughing around.",
  "An HD photo, photorealistic, super detailed, 35mm of me:-) who is sipping coffee at a chic Parisian café on a crisp autumn morning, wearing a stylish wool coat and scarf, the Eiffel Tower in the background, golden leaves scattered on the ground, and people walking by immersed in conversation.",
  "An HD photo, photorealistic, super detailed, 35mm of me:-) who is hiking through a lush green rainforest in South America, wearing an athletic tank top and hiking pants, with misty mountains in the background and exotic birds flying above, sunlight filtering through the dense trees.",
  "An HD photo, photorealistic, super detailed, 35mm of me:-) who is standing on a rooftop in New York City at night, wearing a sleek black blazer and turtleneck, the city skyline illuminated with skyscrapers and bright lights, with a cocktail in hand and a trendy crowd enjoying the evening around him.",
  "An HD photo, photorealistic, super detailed, 35mm of me:-) who is strolling along a tropical beach at sunrise, wearing light swim trunks and a loose shirt, the ocean waves gently rolling onto the shore, with palm trees swaying in the background and a few joggers passing by.",
  "An HD photo, photorealistic, super detailed, 35mm of me:-) who is relaxing by an infinity pool overlooking the ocean at a luxury resort, wearing sunglasses and a casual button-down shirt, the setting sun casting a golden glow on the scene, with a few people swimming in the background and tropical drinks on the side table.",
  "An HD photo, photorealistic, super detailed, 35mm of me:-) who is attending a rooftop garden party in Tokyo at sunset, wearing a sharp navy blue suit, surrounded by modern cityscapes and neon lights, with guests mingling and enjoying sushi and cocktails, the Tokyo Tower in the distance.",
  "An HD photo, photorealistic, super detailed, 35mm of me:-) who is skiing down a snowy mountain in the Swiss Alps on a clear winter morning, wearing a sleek ski jacket and goggles, the sun shining brightly on the pristine white slopes, with other skiers in the background carving down the mountain.",
  "An HD photo, photorealistic, super detailed, 35mm of me:-) who is standing on the deck of a luxury safari lodge in Africa at sunset, wearing a light khaki outfit, with vast savannah stretching out into the distance, a herd of elephants grazing in the background, and the golden light of the setting sun creating a serene atmosphere."
];