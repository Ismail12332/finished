from datetime import datetime
import os
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__, template_folder='templates')
    client = MongoClient(os.getenv("MONGODB_URI"))
    app.db = client.my_database

    @app.route("/", methods=["GET", "POST"])
    def home():
        if request.method == "POST":
            first_name = request.form.get("first_name")
            last_name = request.form.get("last_name")
            city = request.form.get("city")
            phone = request.form.get("phone")
            post = request.form.get("post")
            vessel_name = request.form.get("vessel_name")  # Получаем значение "Vessel Name" из формы

            # Добавляем в базу данных
            project = {
                "first_name": first_name,
                "last_name": last_name,
                "city": city,
                "phone": phone,
                "post": post,
                "sections": [],  # Список разделов
                "vessel_name": vessel_name,  # Сохраняем значение "Vessel Name" в базу данных
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            result = app.db.projects.insert_one(project)
            project_id = result.inserted_id

            print("Entry added:", first_name, last_name, city, phone, post, vessel_name)
            return redirect(url_for('edit_project', project_id=project_id))
        
        projects = app.db.projects.find()
        return render_template("index2.html", projects=projects)



    @app.route("/edit_project/<string:project_id>", methods=["GET"])
    def edit_project(project_id):
        try:
            project_id = ObjectId(project_id)  # Преобразовываем project_id в ObjectId
        except Exception as e:
            # Обработка ошибки, если project_id неверного формата
            return "Invalid project_id", 400

        project = app.db.projects.find_one({"_id": project_id})

        if project is None:
            # Возвращаем сообщение об ошибке, если проект не найден
            return "Project not found", 404

        return render_template("edit_project.html", project=project, project_id=project_id)



    @app.route("/edit_project/<project_id>/add_step", methods=["POST"])
    def add_step(project_id):
        try:
            project_id = ObjectId(project_id)  # Преобразовываем project_id в ObjectId
        except Exception as e:
            # Обработка ошибки, если project_id неверного формата
            return "Invalid project_id", 400

        step_description = request.form.get("step_description")
        section = request.form.get("section")  # Получаем значение раздела из формы

        # Определите, в какой раздел добавить шаг
        section_field = f"{section}_steps"

        try:
            result = app.db.projects.update_one(
                {"_id": project_id},
                {"$push": {section_field: step_description}}
            )
            if result.modified_count == 0:
                # Если ни одна запись не была изменена, возможно, нет проекта с таким project_id
                return "Project not found", 404
        except Exception as e:
            # Обработка других ошибок, например, проблем с базой данных
            print("Error:", e)
            return "An error occurred", 500

        return redirect(url_for("edit_project", project_id=project_id, current_section=section))


    @app.route("/edit_project/<project_id>/delete_step", methods=["POST"])
    def delete_step(project_id):
        try:
            project_id = ObjectId(project_id)
        except Exception as e:
            return "Invalid project_id", 400

        step_to_delete = request.form.get("step_to_delete")
        section = request.form.get("section")
        
        try:
            result = app.db.projects.update_one(
                {"_id": project_id},
                {"$pull": {f"{section}_steps": step_to_delete}}
            )
            if result.modified_count == 0:
                return "Project not found", 404
        except Exception as e:
            print("Error:", e)
            return "An error occurred", 500

        # После успешного удаления шага, перенаправьтесь обратно в текущий раздел
        return redirect(url_for("edit_project", project_id=project_id, current_section=section))

    #тестирую создание---------------------------------------------------------
    #----------------------------------------------------------------
    @app.route("/edit_project/<project_id>/add_section", methods=["POST"])
    def add_section(project_id):
        try:
            project_id = ObjectId(project_id)
        except Exception as e:
            return "Invalid project_id", 400

        section_name = request.form.get("section_name")

        try:
            result = app.db.projects.update_one(
                {"_id": project_id},
                {"$push": {"sections": {"name": section_name, "subsections": []}}}
            )
            if result.modified_count == 0:
                return "Project not found", 404
        except Exception as e:
            print("Error:", e)
            return "An error occurred", 500

        return redirect(url_for("edit_project", project_id=project_id))
    
    @app.route("/edit_project/<project_id>/add_subsection", methods=["POST"])
    def add_subsection(project_id):
        try:
            project_id = ObjectId(project_id)
        except Exception as e:
            return "Invalid project_id", 400

        section_name = request.form.get("section_name")
        subsection_name = request.form.get("subsection_name")

        try:
            result = app.db.projects.update_one(
                {"_id": project_id, "sections.name": section_name},
                {"$push": {"sections.$.subsections": {"name": subsection_name, "cells": []}}}
            )
            if result.modified_count == 0:
                return "Section not found in the project", 404
        except Exception as e:
            print("Error:", e)
            return "An error occurred", 500

        return redirect(url_for("edit_project", project_id=project_id))
    

    @app.route("/edit_project/<project_id>/add_cell", methods=["POST"])
    def add_cell(project_id):
        try:
            project_id = ObjectId(project_id)
        except Exception as e:
            return "Invalid project_id", 400

        section_name = request.form.get("section_name")
        subsection_name = request.form.get("subsection_name")
        cell_name = request.form.get("cell_name")
        cell_description = request.form.get("cell_description")

        try:
            result = app.db.projects.update_one(
                {"_id": project_id},
                {
                    "$push": {
                        "sections.$[section].subsections.$[subsection].cells": {
                            "name": cell_name,
                            "description": cell_description
                        }
                    }
                },
                array_filters=[
                    {"section.name": section_name},
                    {"subsection.name": subsection_name}
                ]
            )
            if result.modified_count == 0:
                return "Section or subsection not found in the project", 404
        except Exception as e:
            print("Error:", e)
            return "An error occurred", 500

        return redirect(url_for("edit_project", project_id=project_id))
    

    @app.route("/edit_project/<project_id>/add_comment/<section_name>/<subsection_name>/<cell_name>", methods=["POST"])
    def add_comment(project_id, section_name, subsection_name, cell_name):
        try:
            project_id = ObjectId(project_id)
        except Exception as e:
            return "Invalid project_id", 400

        cell_comment = request.form.get("cell_comment")

        try:
            result = app.db.projects.update_one(
                {
                    "_id": project_id,
                    "sections.name": section_name,
                    "sections.subsections.name": subsection_name,
                    "sections.subsections.cells.name": cell_name
                },
                {
                    "$set": {
                        "sections.$[section].subsections.$[subsection].cells.$[cell].comment": cell_comment
                    }
                },
                array_filters=[
                    {"section.name": section_name},
                    {"subsection.name": subsection_name},
                    {"cell.name": cell_name}
                ]
            )
            if result.modified_count == 0:
                return "Section, subsection, or cell not found in the project", 404
        except Exception as e:
            print("Error:", e)
            return "An error occurred", 500

        return redirect(url_for("edit_project", project_id=project_id))
    

    @app.route("/edit_project/<project_id>/add_rating/<section_name>/<subsection_name>/<cell_name>", methods=["POST"])
    def add_rating(project_id, section_name, subsection_name, cell_name):
        try:
            project_id = ObjectId(project_id)
        except Exception as e:
            return "Invalid project_id", 400

        cell_rating = request.form.get("cell_rating")

        try:
            result = app.db.projects.update_one(
                {
                    "_id": project_id,
                    "sections.name": section_name,
                    "sections.subsections.name": subsection_name,
                    "sections.subsections.cells.name": cell_name
                },
                {
                    "$set": {
                        "sections.$[section].subsections.$[subsection].cells.$[cell].rating": cell_rating
                    }
                },
                array_filters=[
                    {"section.name": section_name},
                    {"subsection.name": subsection_name},
                    {"cell.name": cell_name}
                ]
            )
            if result.modified_count == 0:
                return "Section, subsection, or cell not found in the project", 404
        except Exception as e:
            print("Error:", e)
            return "An error occurred", 500

        return redirect(url_for("edit_project", project_id=project_id))
    

    #тестирую удаление---------------------------------------------------------
    #----------------------------------------------------------------


    #--удаление раздела
    @app.route("/edit_project/<project_id>/delete_section/<section_name>", methods=["POST"])
    def delete_section(project_id, section_name):
        try:
            project_id = ObjectId(project_id)
        except Exception as e:
            return "Invalid project_id", 400

        try:
            result = app.db.projects.update_one(
                {"_id": project_id},
                {"$pull": {"sections": {"name": section_name}}}
            )
            if result.modified_count == 0:
                return "Section not found in the project", 404
        except Exception as e:
            print("Error:", e)
            return "An error occurred", 500

        return redirect(url_for("edit_project", project_id=project_id))
    

    #--удаление подраздела
    @app.route("/edit_project/<project_id>/delete_subsection/<section_name>/<subsection_name>", methods=["POST"])
    def delete_subsection(project_id, section_name, subsection_name):
        try:
            project_id = ObjectId(project_id)
        except Exception as e:
            return "Invalid project_id", 400

        try:
            result = app.db.projects.update_one(
                {"_id": project_id, "sections.name": section_name},
                {"$pull": {"sections.$.subsections": {"name": subsection_name}}}
            )
            if result.modified_count == 0:
                return "Subsection not found in the project", 404
        except Exception as e:
            print("Error:", e)
            return "An error occurred", 500

        return redirect(url_for("edit_project", project_id=project_id))
    


    #--удаление ячейки
    @app.route("/edit_project/<project_id>/delete_cell/<section_name>/<subsection_name>/<cell_name>", methods=["POST"])
    def delete_cell(project_id, section_name, subsection_name, cell_name):
        try:
            project_id = ObjectId(project_id)
        except Exception as e:
            return "Invalid project_id", 400

        try:
            # Находим проект по идентификатору
            project = app.db.projects.find_one({"_id": project_id})

            # Находим раздел, подраздел и ячейку, которую нужно удалить
            section_index = None
            subsection_index = None
            cell_index = None

            for i, section in enumerate(project["sections"]):
                if section["name"] == section_name:
                    section_index = i
                    for j, subsection in enumerate(section["subsections"]):
                        if subsection["name"] == subsection_name:
                            subsection_index = j
                            for k, cell in enumerate(subsection["cells"]):
                                if cell["name"] == cell_name:
                                    cell_index = k

            # Если раздел, подраздел и ячейка найдены, удаляем ячейку
            if section_index is not None and subsection_index is not None and cell_index is not None:
                del project["sections"][section_index]["subsections"][subsection_index]["cells"][cell_index]

                # Обновляем документ проекта в базе данных
                app.db.projects.update_one({"_id": project_id}, {"$set": project})

            else:
                return "Cell not found in the project", 404

        except Exception as e:
            print("Error:", e)
            return "An error occurred", 500

        return redirect(url_for("edit_project", project_id=project_id))
    

    # -- удаление комментария
    @app.route("/edit_project/<project_id>/delete_comment/<section_name>/<subsection_name>/<cell_name>", methods=["POST"])
    def delete_comment(project_id, section_name, subsection_name, cell_name):
        try:
            project_id = ObjectId(project_id)
        except Exception as e:
            return "Invalid project_id", 400

        try:
            result = app.db.projects.update_one(
                {
                    "_id": project_id,
                    "sections.name": section_name,
                    "sections.subsections.name": subsection_name,
                    "sections.subsections.cells.name": cell_name
                },
                {
                    "$unset": {
                        "sections.$[section].subsections.$[subsection].cells.$[cell].comment": ""
                    }
                },
                array_filters=[
                    {"section.name": section_name},
                    {"subsection.name": subsection_name},
                    {"cell.name": cell_name}
                ]
            )
            if result.modified_count == 0:
                return "Section, subsection, or cell not found in the project", 404
        except Exception as e:
            print("Error:", e)
            return "An error occurred", 500

        return redirect(url_for("edit_project", project_id=project_id))

    
    # #--удаление рейтинга
    @app.route("/edit_project/<project_id>/delete_rating/<section_name>/<subsection_name>/<cell_name>", methods=["POST"])
    def delete_rating(project_id, section_name, subsection_name, cell_name):
        try:
            project_id = ObjectId(project_id)
        except Exception as e:
            return "Invalid project_id", 400

        try:
            # Находим проект по идентификатору
            project = app.db.projects.find_one({"_id": project_id})

            # Находим раздел, подраздел, ячейку и рейтинг, который нужно удалить
            section_index = None
            subsection_index = None
            cell_index = None
            rating_index = None

            for i, section in enumerate(project["sections"]):
                if section["name"] == section_name:
                    section_index = i
                    for j, subsection in enumerate(section["subsections"]):
                        if subsection["name"] == subsection_name:
                            subsection_index = j
                            for k, cell in enumerate(subsection["cells"]):
                                if cell["name"] == cell_name:
                                    cell_index = k
                                    if "rating" in cell:
                                        rating_index = "rating"

            # Если раздел, подраздел, ячейка и рейтинг найдены, удаляем рейтинг
            if (
                section_index is not None
                and subsection_index is not None
                and cell_index is not None
                and rating_index is not None
            ):
                del project["sections"][section_index]["subsections"][subsection_index]["cells"][cell_index][rating_index]

                # Обновляем документ проекта в базе данных
                app.db.projects.update_one({"_id": project_id}, {"$set": project})

            else:
                return "Rating not found in the project", 404

        except Exception as e:
            print("Error:", e)
            return "An error occurred", 500

        return redirect(url_for("edit_project", project_id=project_id))


    return app
