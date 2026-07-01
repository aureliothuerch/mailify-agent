from agents.mail_graph import build_mail_graph

graph = build_mail_graph().get_graph()
graph.draw_mermaid_png(output_file_path="graph.png")
print("Wrote graph.png")
