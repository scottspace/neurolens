function handleCredentialResponse(response) {
  // This function will be called after the user successfully signs in.
  fetch('/auth/google', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ id_token: response.credential })
  })
  .then(response => response.json())
  .then(data => {
    // Handle response data (e.g., save user info or redirect)
      console.log('Success:', data);
      redirect("/home");
      
  })
  .catch((error) => {
    console.error('Error:', error);
  });
}

function redirect (url) {
    var ua        = navigator.userAgent.toLowerCase(),
        isIE      = ua.indexOf('msie') !== -1,
        version   = parseInt(ua.substr(4, 2), 10);

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
    }
}
