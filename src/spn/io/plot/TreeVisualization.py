from ete3 import Tree, TreeStyle, faces, AttrFace, TextFace, NodeStyle
from spn.io.Text import spn_to_str_equation

from spn.structure.Base import Sum, Leaf, Product


def spn_to_ete(spn, context=None, unroll=False):
    tree = Tree()
    tree.name = spn.name

    if isinstance(spn, Sum):
        tree.name = "Σ"
    if isinstance(spn, Product):
        tree.name = "Π"

    queue = []

    if not isinstance(spn, Leaf):
        for i, child in enumerate(spn.children):
            if unroll:
                if child in queue:
                    return '-> ' + spn.id
                else:
                    queue.append(child)
            c = spn_to_ete(child, context=context, unroll=unroll)
            if isinstance(spn, Sum):
                c.support = spn.weights[i]
            tree.add_child(c)
    else:
        tree.name = spn_to_str_equation(spn, feature_names=context.feature_names)

    return tree


def get_newick(spn, context=None, unroll_dag=False):
    tree = spn_to_ete(spn, context, unroll_dag)
    return tree.write(format=1)


def plot_spn(spn, context=None, unroll=False, file_name=None):
    lin_style = TreeStyle()

    def my_layout(node):

        style = NodeStyle()
        style["size"] = 0
        style["vt_line_color"] = "#A0A0A0"
        style["hz_line_color"] = "#A0A0A0"
        style["vt_line_type"] = 0  # 0 solid, 1 dashed, 2 dotted
        style["hz_line_type"] = 0
        node.set_style(style)

        if node.is_leaf():
            name_face = AttrFace("name")
        else:
            name_face = TextFace(node.name, fsize=14, ftype='Times')
            if node.name == 'Σ':
                for child in node.children:
                    label = TextFace(round(child.support, 3), fsize=6)
                    child.add_face(label, column=1, position="branch-bottom")
        faces.add_face_to_node(name_face, node, column=1, position="branch-right")

    lin_style.layout_fn = my_layout
    lin_style.show_leaf_name = False
    lin_style.show_scale = False

    tree = spn_to_ete(spn, context, unroll)

    if file_name is not None:
        return tree.render(file_name, tree_style=lin_style)
