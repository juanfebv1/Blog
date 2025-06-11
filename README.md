# Project API Documentation

## Overview

This project is a blog-like RESTful API built using Django and Django REST Framework (DRF). It supports user registration, post creation with permission controls, likes, and comments. Users can be bloggers or admins, and posts can be shared publicly, within teams, or with authenticated users.


## Authentication

### Login
 `[GET/POST] /api-auth/` — DRF's built-in login/logout views.
  
### Register
You can register a new user. You must be unauthenticated to register. 
    `[POST] /api/register/`
**Request body:**
  ```json
    {
        "email" : "user@email.com",
        "username" : "user",
        "password" : "1234"
    }
  ```

## Admin

* `GET /admin/` — Django admin interface.

## Posts
### Create a post
Authenticated users can create a new post by sending a request to:
 `[POST] /api/posts/`

**Request body:**
  ```json
    {
        "title" : "My post",
        "content" : "Some content",
        "public_permission" : true,
        "authenticated_permission" : 1,
        "team_permission" : 2
    }
  ```
You can define access control for your post using the following fields:

| Field                      | Type    | Description                                                             |
| -------------------------- | ------- | ----------------------------------------------------------------------- |
| `public_permission`        | Boolean | If `true`, the post is visible to anyone (including anonymous users).   |
| `authenticated_permission` | Integer | Minimum access level required for authenticated users.                  |
| `team_permission`          | Integer | Minimum access level required for users in the same team as the author. |


For authenticated and team permissions, access level values are:

* `0 = No access`
* `1 = Read Only`
* `2 = Read and Write`

If no permissions are set, the post defaults to private.
The system ensures that permission levels maintain a valid hierarchy:
`public_permission ≤ authenticated_permission ≤ team_permission.`


### List accessible posts
Users can get a list of all accessible posts with the request
`[GET] /api/posts/` 
**Response:**
```json
{
    "prev page": null,
    "next page": null,
    "current page": 1,
    "pages": 1,
    "count": 4,
    "results": [
        {
            "id": 4,
            "title": "My post",
            "content": "Some content",
            "username": "user1",
            "posted_on": "2025-06-10T20:27:23.975842Z",
            "authenticated_permission": 0,
            "team_permission": 0,
            "public_permission": false
        },
        // ...
    ]
}
```
* Anonymous users see only `public_permission=True` posts.
* Authenticated users see:

  * Their own posts.
  * Posts from same team with `team_permission >= 1`.
  * Posts with `authenticated_permission >= 1`.
  * Public posts.
* Admins can see all posts.

### Get a single post by id
User can retrieve a post by adding the `id` as a parameter, only if the post is accessible to the user.
`[GET] /api/posts/<id>/` 
**Response:**
```json
{
    "id": 4,
    "title": "My post",
    "content": "Some content",
    "username": "user1",
    "posted_on": "2025-06-10T20:27:23.975842Z",
    "authenticated_permission": 0,
    "team_permission": 0,
    "public_permission": false
}
```
The request will return 403 Forbidden if the post exists but is not accessible, and 404 Not Found if the post does not exist.
 

### Update a post 
Update a post by its `id`. User must have **write access** to the post. All attributes of a post can be updated, including permission levels.
`[PUT/PATCH] /api/posts/<id>/` 
**Request body:**
```json
{
  "title": "Updated title",
  "content": "Updated content",
  "public_permission": true,
  "authenticated_permission": 1,
  "team_permission": 2
}
```

### Delete a post
Delete a post by its `id`. User must have **write access** to the post.
`[DELETE] /api/posts/<id>/`

## Likes

### List likes
* List likes filtered by accessible posts.
`[GET] /api/likes/` 
* List likes filtered by a specific post:
`[GET] /api/likes/?post=<id>/` 
* List likes filtered by a specific user:
`[GET] /api/likes/?user=<id>/` 

**Response:**
```json
{
    "prev page": null,
    "next page": null,
    "current page": 1,
    "pages": 1,
    "count": 2,
    "results": [
        {
            "id": 2,
            "liked_at": "2025-06-10T21:39:01.332302Z",
            "post": 3,
            "user": 2
        },
        // ...
    ]
}
```

### Like a post
Authenticated users can like an accessible post.
`[POST] /api/likes/`
  **Request body:**
  ```json
    {
        "post" : 4
    }
  ```
The request will return 403 Forbidden if the post exists but is not accessible, and 400 Bad Request if the post does not exist. 

### Unlike a post
Owner of a like can unlike a post by adding the `id` of the like.
`[DELETE] /api/likes/<id>/`


## Comments

### List comments
* List comments filtered by accessible posts.
`[GET] /api/comments/` 
* List comments filtered by a specific accesible post:
`[GET] /api/comments/?post=<id>/` 
* List comments filtered by a specific user:
`[GET] /api/comments/?user=<id>/` 

**Response:**
```json
{
    "prev page": null,
    "next page": null,
    "current page": 1,
    "pages": 1,
    "count": 2,
    "results": [
        {
            "id": 1,
            "post": 3,
            "username": "felipe",
            "content": "Lorem"
        },
        // ...
    ]
}
```

### Comment a post
Authenticated users can comment an accessible post.
`[POST] /api/comments/`
  **Request body:**
  ```json
    {
        "post" : 4,
        "content" : "Some comment"
    }
  ```
The request will return 403 Forbidden if the post exists but is not accessible, and 400 Bad Request if post does not exist. 

### Delete a comment
Owner of a comment can delete it by adding the `id` of the comment.
`[DELETE] /api/comments/<id>/`





