@app.route("/friends")
def friends_page():
    if "user_id" not in session:  
        return redirect("/login")  # chưa login thì không xem friend list
    
    return render_template("friends.html")  # session tự truyền vào file