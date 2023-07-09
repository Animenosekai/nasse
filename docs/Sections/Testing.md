
# Testing Section API Reference

This file lists and explains the different endpoints available in the Testing section.

# Untitled

This is a cool testing endpoint

```http
* /test
```

> [test.py](../../test.py#L5)

### Authentication

There is no authentication rule defined

### Example

<!-- tabs:start -->


<details>
    <summary>cURL Example</summary>

#### **cURL**

```bash
curl -X * "/test"
```

</details>


<details>
    <summary>JavaScript Example</summary>

#### **JavaScript**

```javascript
fetch("/test", {
    method: "*"
})
.then((response) => {response.json()})
.then((response) => {
    if (response.success) {
        console.info("Successfully requested for /test")
        console.log(response.data)
    } else {
        console.error("An error occured while requesting for /test, error: " + response.error)
    }
})
```

</details>


<details>
    <summary>Python Example</summary>

#### **Python**

```python
import requests
r = requests.request("*", "/test")
if r.status_code >= 400 or not r.json()["success"]:
    raise ValueError("An error occured while requesting for /test, error: " + r.json()["error"])
print("Successfully requested for /test")
print(r.json()["data"])
```

</details>
<!-- tabs:end -->

[Return to the Index](../Getting%20Started.md#index)