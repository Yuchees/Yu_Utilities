#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data classification and dimensionality reduction.
@author: Yu Che
"""
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime
from sklearn import manifold
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.cluster import AffinityPropagation


# noinspection PyRedundantParentheses,PyUnboundLocalVariable
class MdsPlot(object):
    """
    This class is used to proceed a plot after clustering and
    scaling methods.
    """
    def __init__(self):
        self.df = pd.DataFrame()
        self.data_df = pd.DataFrame()
        self.selected_df = pd.DataFrame()
        self.similarities = None
        self.features = None
        self.size = None
        self.pos_df = pd.DataFrame()

    def data_retrieve(self, path, size, descriptors):
        """
        Data set retrieve function.

        :param path: The path for input data file.
        :param size: The range of columns in data set.
        :param descriptors: Variables will be used in the plot.
        :type path: str
        :type size: tuple
        :type descriptors: list
        :return: None
        """
        print('Reading data frame...')
        self.size = size
        # Reading data frame
        file_format = path.split('.')[-1]
        if file_format == 'csv':
            self.df = pd.read_csv(path)
        elif file_format == ('xls' or 'xlsx'):
            self.df = pd.read_excel(path)
        elif file_format == 'pkl':
            self.df = pd.read_pickle(path)
        else:
            print('Error! Please select the correct format file.')
            exit()
        # Selecting the range of input data
        self.data_df = self.df.iloc[:, size[0]:size[1]]
        # Delete no numerical data to avoid error in normalization
        for column in self.data_df.columns:
            if self.data_df.dtypes[column] != ('float64' or 'int64'):
                self.data_df = self.data_df.drop(column, axis=1)
        print('Normalizing...')
        # Normalization
        self.features = MinMaxScaler().fit_transform(self.data_df.values)
        # Merge descriptors into data_df
        self.data_df = self.data_df.merge(
            pd.DataFrame(self.df[descriptors]), left_index=True,
            right_index=True
        )
        print(
            'Finished!\n'
            'Selected data frame: self.data_df\n'
            'Descriptors matrix:  self.features\n'
            'Descriptor shape:    {}'.format(self.features.shape)
        )

    def affinity_propagation_cluster(self):
        """
        Using affinity propagation to cluster the data set. The cluster
        information is written in the 'AffinityPropagation' column.

        :return: None
        """
        print('Affinity propagation starting...')
        start = datetime.now()
        af = AffinityPropagation(
            max_iter=30000, convergence_iter=70, preference=None
        ).fit(self.features)
        cluster_centers_indices = af.cluster_centers_indices_
        df_labels = pd.DataFrame(af.labels_)
        n_clusters = len(cluster_centers_indices)
        # Merge cluster information into origin data frame
        self.data_df = self.data_df.merge(
            df_labels, left_index=True, right_index=True
        )
        self.data_df.rename(columns={0: 'AffinityPropagation'}, inplace=True)
        print(
            'Finished!\n'
            'Estimated number of clusters: {}\n'
            'Total time:{}'.format(n_clusters, (datetime.now() - start))
        )

    def cluster_structure_selection(self, descriptor):
        """
        Choosing the lowest value for selected descriptor in each cluster.

        :param descriptor: One selected variable in the data frame.
        :type descriptor: str
        :return: None
        """
        # The lowest lattice energy for each cluster
        for i in range(0, self.data_df.AffinityPropagation.max() + 1):
            df_cluster = self.data_df[self.data_df['AffinityPropagation'] == i]
            selected_structure = df_cluster[
                df_cluster[descriptor] == df_cluster[descriptor].min()
                ]
            self.selected_df = self.selected_df.append(selected_structure)
        # Rearrange index
        self.selected_df.index = range(len(self.selected_df))

    def dim_reduction_calculation(self, method):
        """
        Using non-linear dimensionality reduction method for the selected data
        to calculate 2D coordinators.
        The coordinator information is written in 'pos0' and 'pos1' columns.

        :param method: The chosen method for reduction. Supported MDS, t-SNE,
        isomap and lle.
        :type method: str
        :return: None
        """
        print('Distance calculation...')
        start = datetime.now()
        # Selecting the data matrix
        features = self.selected_df.iloc[
                   :, self.size[0]:(self.size[1] - 1)].values
        scaled_features = MinMaxScaler().fit_transform(features)
        # Distance calculation
        distance = euclidean_distances(scaled_features)
        self.similarities = distance / distance.max()
        print('Dimensionality reduction starting...')
        seed = np.random.RandomState(seed=0)
        if method == 'mds':
            mds = manifold.MDS(
                n_components=2, max_iter=30000, random_state=seed,
                eps=1e-12, dissimilarity="precomputed"
            )
            pos = mds.fit(self.similarities).embedding_
        elif method == 'tsne':
            tsne = manifold.TSNE(
                n_components=2, n_iter=30000, random_state=seed,
                min_grad_norm=1e-12, init='pca'
            )
            pos = tsne.fit(scaled_features).embedding_
        elif method == 'isomap':
            isomap = manifold.Isomap(
                n_components=2, n_neighbors=12, max_iter=30000,
            )
            pos = isomap.fit(scaled_features).embedding_
        elif method == 'lle':
            lle = manifold.locally_linear_embedding(
                X=scaled_features, n_neighbors=12,
                n_components=2, max_iter=30000, random_state=seed
            )
            pos = lle[0]
        self.pos_df = pd.DataFrame(data=pos, columns=['pos0', 'pos1'])
        self.selected_df = self.selected_df.merge(
            self.pos_df, left_index=True, right_index=True
        )
        print(
            'Finished.\n'
            'Distance matrix:     self.similarities\n'
            'Selected data frame: self.selected_df\n'
            'Total time:{}'.format(datetime.now() - start)
        )

    def plot(self, title, size, color, tag=(), range_line=(),
             colorscale='RdBu', lines=False, text='Structure'):
        """
        This function is based on plotly API to generate a scatter plot for
        non-linear dimensionality reduction.
        Using plotly function to generate the plot in notebook.

        :param title: The plot title.
        :param text:  The descriptor will be shown in the text part in plot.
        :param size: The name of a descriptor to scale the scatter size.
        :param color: The name of a descriptor to scale the colour.
        :param lines: Enable lines to describe the similarity.
        :param tag: The name of selected structures shown in diamond style.
        :param range_line: The range of length for similarity lines
        :param colorscale: Sets the colorscale
        :type title: str
        :type size: str
        :type color: str
        :type tag: tuple
        :type range_line: tuple
        :type colorscale: str or list
        :return: Plotly figure object.
        """
        print('Starting...')
        start = datetime.now()
        tag_list = list(
            self.selected_df[self.selected_df.Structure.isin(list(tag))].index
        )
        # Generating the network line part
        if lines:
            print('Building the line segment...')
            edge_trace = go.Scatter(
                x=[],
                y=[],
                line=dict(width=0.5, color='rgb(134, 134, 134)'),
                opacity=0.7,
                hoverinfo='none',
                mode='lines'
            )
            # Generate the start-stop point coordinates
            segments = []
            n_space = len(self.similarities)
            for i in range(n_space):
                for j in range(n_space):
                    # Limited the line length
                    if range_line[0] < self.similarities[i, j] < range_line[1]:
                        p1 = [self.pos_df.iloc[i, 0], self.pos_df.iloc[i, 1]]
                        p2 = [self.pos_df.iloc[j, 0], self.pos_df.iloc[j, 1]]
                        segments.append([p1, p2])
            # Adding each line's coordinates into plot
            for edge in segments:
                x0, y0 = edge[0]
                x1, y1 = edge[1]
                edge_trace['x'] += tuple([x0, x1, None])
                edge_trace['y'] += tuple([y0, y1, None])
        # Scatter plot
        print('Building the scatter segment...')
        # Circle points and hiding the selected points
        trace0 = go.Scatter(
            x=self.selected_df.loc[:, 'pos0'],
            y=self.selected_df.loc[:, 'pos1'],
            text=self.selected_df.loc[:, text],
            mode='markers',
            selectedpoints=tag_list,
            selected=dict(marker=dict(opacity=0)),
            unselected=dict(marker=dict(opacity=1)),
            marker=dict(
                symbol='circle',
                size=(8 + self.selected_df.loc[:, size]),
                color=self.selected_df.loc[:, color],
                colorscale=colorscale,
                colorbar=dict(
                    thicknessmode='pixels',
                    thickness=20,
                    title='Lattice energy'
                ),
                reversescale=True,
                showscale=True
            )
        )
        # Diamond points and hiding the unselected points
        trace1 = go.Scatter(
            x=self.selected_df.loc[:, 'pos0'],
            y=self.selected_df.loc[:, 'pos1'],
            text=self.selected_df.loc[:, text],
            mode='markers',
            selectedpoints=tag_list,
            selected=dict(marker=dict(opacity=1)),
            unselected=dict(marker=dict(opacity=0)),
            marker=dict(
                symbol='diamond',
                size=(8 + self.selected_df.loc[:, size]),
                color=self.selected_df.loc[:, color],
                colorscale=colorscale,
                reversescale=True,
                showscale=False
            )
        )
        # Hidden all axis
        axis_template = dict(
            showgrid=False,
            zeroline=False,
            showline=False,
            showticklabels=False,
        )
        layout = go.Layout(
            title=title,
            hovermode='closest',
            xaxis=axis_template,
            yaxis=axis_template,
            showlegend=False
        )
        # The plot function
        if lines:
            plot_fig = go.Figure(
                data=[trace0, trace1, edge_trace], layout=layout)
        else:
            plot_fig = go.Figure(data=[trace0, trace1], layout=layout)
        print(
            'Finished!\n'
            'Total time:{}'.format(datetime.now() - start)
        )
        return plot_fig


if __name__ == '__main__':
    # Test script
    plot = MdsPlot()
    plot.data_retrieve(
        path='../4EPK/T2.csv', size=(None, 23),
        descriptors=['Structure', 'Final_lattice_E', 'CH4_Del(65-5.8bar)']
    )
    plot.affinity_propagation_cluster()
    plot.cluster_structure_selection(descriptor='Final_lattice_E')
    plot.dim_reduction_calculation('lle')
    fig = plot.plot(
        title='T2 MDS plot', size='CH4_Del(65-5.8bar)',
        color='Final_lattice_E', text='Structure',
        tag=('job_00014', 'job_00054', 'job_00120', 'job_00186')
    )
