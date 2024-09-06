const SESSION = 'neuro_session_info';

function get_session() {
  val = localStorage.getItem(SESSION);
  if (val == null) val = {};
  return val;
}

function save_session(info) {
  localStorage.setItem(SESSION, info);
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
      console.log('Success:', data);
      // Redirect to the homepage or handle the user session
      // store our session key for communicating with our server
      save_session(data);
      redirect("/home?s=" + data['sid'])
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