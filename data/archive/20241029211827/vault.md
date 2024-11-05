USER: This is a test, is it locally running?
AI: Traceback (most recent call last):
  File "X:\Documents\Python Projects\ScriptsEditor\venv\Lib\site-packages\httpx\_transports\default.py", line 69, in map_httpcore_exceptions
    yield
  File "X:\Documents\Python Projects\ScriptsEditor\venv\Lib\site-packages\httpx\_transports\default.py", line 233, in handle_request
    resp = self._pool.handle_request(req)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "X:\Documents\Python Projects\ScriptsEditor\venv\Lib\site-packages\httpcore\_sync\connection_pool.py", line 216, in handle_request
    raise exc from None
  File "X:\Documents\Python Projects\ScriptsEditor\venv\Lib\site-packages\httpcore\_sync\connection_pool.py", line 196, in handle_request
    response = connection.handle_request(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "X:\Documents\Python Projects\ScriptsEditor\venv\Lib\site-packages\httpcore\_sync\connection.py", line 99, in handle_request
    raise exc
  File "X:\Documents\Python Projects\ScriptsEditor\venv\Lib\site-packages\httpcore\_sync\connection.py", line 76, in handle_request
    stream = self._connect(request)
             ^^^^^^^^^^^^^^^^^^^^^^
  File "X:\Documents\Python Projects\ScriptsEditor\venv\Lib\site-packages\httpcore\_sync\connection.py", line 122, in _connect
    stream = self._network_backend.connect_tcp(**kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "X:\Documents\Python Projects\ScriptsEditor\venv\Lib\site-packages\httpcore\_backends\sync.py", line 205, in connect_tcp
    with map_exceptions(exc_map):
  File "C:\Users\AxelFC\AppData\Local\Programs\Python\Python311\Lib\contextlib.py", line 158, in __exit__
    self.gen.throw(typ, value, traceback)
  File "X:\Documents\Python Projects\ScriptsEditor\venv\Lib\site-packages\httpcore\_exceptions.py", line 14, in map_exceptions
    raise to_exc(exc) from exc
httpcore.ConnectError: [WinError 10061] No se puede establecer una conexión ya que el equipo de destino denegó expresamente dicha conexión

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "X:\Documents\Python Projects\ScriptsEditor\venv\Lib\site-packages\openai\_base_client.py", line 952, in _request
    response = self._client.send(
               ^^^^^^^^^^^^^^^^^^
  File "X:\Documents\Python Projects\ScriptsEditor\venv\Lib\site-packages\httpx\_client.py", line 914, in send
    response = self._send_handling_auth(
               ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "X:\Documents\Python Projects\ScriptsEditor\venv\Lib\site-packages\httpx\_client.py", line 942, in _send_handling_auth
    response = self._send_handling_redirects(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "X:\Documents\Python Projects\ScriptsEditor\venv\Lib\site-packages\httpx\_client.py", line 979, in _send_handling_redirects
    response = self._send_single_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "X:\Documents\Python Projects\ScriptsEditor\venv\Lib\site-packages\httpx\_client.py", line 1015, in _send_single_request
    response = transport.handle_request(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "X:\Documents\Python Projects\ScriptsEditor\venv\Lib\site-packages\httpx\_transports\default.py", line 232, in handle_request
    with map_httpcore_exceptions():
  File "C:\Users\AxelFC\AppData\Local\Programs\Python\Python311\Lib\contextlib.py", line 158, in __exit__
    self.gen.throw(typ, value, traceback)
  File "X:\Documents\Python Projects\ScriptsEditor\venv\Lib\site-packages\httpx\_transports\default.py", line 86, in map_httpcore_exceptions
    raise mapped_exc(message) from exc
httpx.ConnectError: [WinError 10061] No se puede establecer una conexión ya que el equipo de destino denegó expresamente dicha conexión

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "X:\Documents\Python Projects\ScriptsEditor\src\models\ai_assistant.py", line 415, in <module>
    main()
  File "X:\Documents\Python Projects\ScriptsEditor\src\models\ai_assistant.py", line 403, in main
    chat_loop(user_input, client, model_path, system_prompt, session_id)
  File "X:\Documents\Python Projects\ScriptsEditor\src\models\ai_assistant.py", line 163, in chat_loop
    response = client.chat.completions.create(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "X:\Documents\Python Projects\ScriptsEditor\venv\Lib\site-packages\openai\_utils\_utils.py", line 277, in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "X:\Documents\Python Projects\ScriptsEditor\venv\Lib\site-packages\openai\resources\chat\completions.py", line 590, in create
    return self._post(
           ^^^^^^^^^^^
  File "X:\Documents\Python Projects\ScriptsEditor\venv\Lib\site-packages\openai\_base_client.py", line 1240, in post
    return cast(ResponseT, self.request(cast_to, opts, stream=stream, stream_cls=stream_cls))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "X:\Documents\Python Projects\ScriptsEditor\venv\Lib\site-packages\openai\_base_client.py", line 921, in request
    return self._request(
           ^^^^^^^^^^^^^^
  File "X:\Documents\Python Projects\ScriptsEditor\venv\Lib\site-packages\openai\_base_client.py", line 976, in _request
    return self._retry_request(
           ^^^^^^^^^^^^^^^^^^^^
  File "X:\Documents\Python Projects\ScriptsEditor\venv\Lib\site-packages\openai\_base_client.py", line 1053, in _retry_request
    return self._request(
           ^^^^^^^^^^^^^^
  File "X:\Documents\Python Projects\ScriptsEditor\venv\Lib\site-packages\openai\_base_client.py", line 976, in _request
    return self._retry_request(
           ^^^^^^^^^^^^^^^^^^^^
  File "X:\Documents\Python Projects\ScriptsEditor\venv\Lib\site-packages\openai\_base_client.py", line 1053, in _retry_request
    return self._request(
           ^^^^^^^^^^^^^^
  File "X:\Documents\Python Projects\ScriptsEditor\venv\Lib\site-packages\openai\_base_client.py", line 986, in _request
    raise APIConnectionError(request=request) from err
openai.APIConnectionError: Connection error.
[0m
