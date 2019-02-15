#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 19 10:19:00 2018

@author: Yu Che
"""
import os
import shutil
import re


# noinspection PyBroadException
class GaussianInout:
    def __init__(self, method, mol, seq, path='../../Documents'):
        self.gauss_method = method
        self.mol_group = '{}_{}'.format(mol, seq)
        # Gaussian16 header and barkla bash template
        self.header = './header_{}'.format(method)
        self.bash = './bash_template'
        # Molecular coordinators
        self.mol_folder = '{}/{}/{}'.format(path, mol, seq)
        # Gaussian16 input and output folder
        self.input_folder = '{}/input_{}'.format(path, method)
        self.output_folder = '{}/output_{}'.format(path, method)
        # Error and negative frequency folder
        # self.check_out_folder = '{}'.format(self.output_folder)
        self.check_target_folder = ('{}/output_{}/result'.format(path, method))
        # Normal terminated results
        self.normal_folder = self.output_folder + '/' + self.mol_group
        self.chk_path = ('%Chk=/users/psyche/volatile/gaussian'
                         '/chk/{}/{}/'.format(method, mol))

    def setup_target_folder(self, folder):
        if folder.endswith('/'):
            folder = folder[:-1]
        self.check_target_folder = folder

    def setup_out_folder(self, folder):
        if folder.endswith('/'):
            folder = folder[:-1]
            self.check_out_folder = folder

    def setup_chk_path(self, chk_path):
        self.chk_path = chk_path

    def info(self, info):
        """
        Check and print all variables before run any functions.
        """
        if info in ['all']:
            print('Gaussian16 {}'.format(self.gauss_method))
        if info in ['all', 'input']:
            print(
                'Header template: {}\n'
                'Checkpoint line: {}\n'
                'Molecular:       {}\n'
                'Gaussian input:  {}/{}'.format(
                    self.header,
                    self.chk_path,
                    self.mol_folder,
                    self.input_folder,
                    self.mol_group
                )
            )
        if info in ['all', 'neg', 'error']:
            print('Normal output:   {}'.format(self.normal_folder))
        if info in ['all', 'neg']:
            print(
                'Neg_freq output folder: {}\n'
                'Targeted folder: {}'.format(
                    self.check_out_folder,
                    self.check_target_folder
                )
            )
        if info in ['all', 'error']:
            print(
                'Error output folder: {}\n'
                'Targeted folder: {}'.format(
                    self.check_out_folder,
                    self.check_target_folder
                )
            )
        if info in ['all', 'error_input']:
            print(
                'Error input folder: {}\n'
                'Error check folder: {}'.format(
                    (self.input_folder + '/' +
                     self.check_target_folder.split('/')[-1]),
                    self.check_target_folder
                )
            )
        if info not in ['all', 'input', 'neg', 'error', 'error_input']:
            print(
                'The info variable must belong to: all, input, neg, error,'
                'error_input.'
            )

    def prep_input(self):
        """
        Until now, this function can only recognise .mol and .xyz format files.
        Please run info('input') first to check the path.
        """
        print('Processing...')
        # Create folders for origin Gaussian input files
        input_origin_folder = self.input_folder + '/' + self.mol_group
        if not os.path.exists(self.input_folder):
            os.mkdir(self.input_folder)
        if not os.path.exists(input_origin_folder):
                os.mkdir(input_origin_folder)
        with open(self.header, 'r') as header:
            template = tuple(header.readlines())
        # Generate Gaussian input data for all molecules
        for file in os.listdir(self.mol_folder):
            input_data = list(template)
            # Get the molecular name
            name = file.split('.')[0]
            # Edit the checkpoint line
            input_data[2] = self.chk_path + name + '.chk\n'
            # Read molecule file
            molecular_file = self.mol_folder + '/' + file
            with open(molecular_file, 'r') as data:
                # Get all atoms coordinates
                # For mol format
                if file.endswith('.mol'):
                    for line in data:
                        try:
                            if line[35] == '0':
                                coordinates = '{}   {}\n'.format(
                                    line[31:33],
                                    line[1:30]
                                )
                                input_data.append(coordinates)
                        except:
                            pass
                # For xyz format
                elif file.endswith('.xyz'):
                    for line in data:
                        try:
                            if line[0].isalpha():
                                input_data.append(line)
                        except:
                            pass
                else:
                    print('Waring!\n{} is not a MOL or XYZ format file!'.format(
                        file))
                    break
            # Adding terminate line
            input_data.append('\n')
            # Writing data into a gjf file
            input_path = '{}/{}.gjf'.format(input_origin_folder, name)
            with open(input_path, 'w') as input_file:
                input_file.writelines(input_data)
        print('Finished!')

    def check_freq(self):
        # Checking output files
        print('Targeted folder: {}'.format(self.check_target_folder))
        for file in os.listdir(self.check_target_folder):
            if not file.endswith('.out'):
                print('Error!\n{} is not a Gaussian out file!'.format(file))
                break
            path = self.check_target_folder + '/' + file
            with open(path, 'r') as gauss_out:
                for line in gauss_out:
                    # Checking the frequencies
                    if line.startswith(' Frequencies'):
                        data = re.split(r'\s+', line)
                        # Normal terminated jobs
                        if float(data[3]) > 0:
                            if not os.path.exists(self.normal_folder):
                                os.mkdir(self.normal_folder)
                                print('The final out files: {}'.format(
                                    self.normal_folder))
                            # Move to the final folder
                            shutil.move(path, self.normal_folder)
                            break
                        # Negative frequencies
                        elif float(data[3]) < 0:
                            check_out_folder = self.output_folder + '/neg_freq'
                            if not os.path.exists(check_out_folder):
                                os.mkdir(check_out_folder)
                                print(check_out_folder)
                            # Move to negative frequencies folder
                            shutil.move(path, check_out_folder)
                            break
        print('Finished!')

    def check_error(self):
        # Checking the error for output files
        print('Targeted folder: {}'.format(self.check_target_folder))
        for file in os.listdir(self.check_target_folder):
            if not file.endswith('.out'):
                print('Error!\n{} is not a Gaussian out file!'.format(file))
                break
            path = self.check_target_folder + '/' + file
            with open(path, 'r') as gauss_out:
                error_line = gauss_out.readlines()[-4:-3][0]
            # Checking the error indicator
            if error_line.startswith(' Error termination'):
                error = re.split(r'[/.]', error_line)[-3][1:]
                # Creating a new folder for different categories of error
                new_path = self.output_folder + '/error_' + error
                if not os.path.exists(new_path):
                    os.mkdir(new_path)
                    print(new_path)
                shutil.move(path, new_path)
        print('Finished!')

    def error_or_freq_input(self):
        # Generating input fies for error and negative frequency results.
        print('Targeted folder: {}'.format(self.check_target_folder))
        error_list = os.listdir(self.check_target_folder)
        with open(self.header, 'r') as header:
            template = tuple(header.readlines())
        for file in error_list:
            input_data = list(template)
            name = file.split('.')[0]
            # Edit checkpoint line
            input_data[2] = self.chk_path + name + '.chk\n'
            # Creating folder and writing the input files
            input_folder_error = (self.input_folder + '/' +
                                  self.check_target_folder.split('/')[-1])
            if not os.path.exists(input_folder_error):
                os.mkdir(input_folder_error)
            input_file_path = input_folder_error + '/{}.gjf'.format(name)
            with open(input_file_path, 'w') as input_file:
                input_file.writelines(input_data)
        print('Finished!')


if __name__ == '__main__':
    gauss_function = GaussianInout(method='PM7', mol='dyes', seq='dimer')
    gauss_function.info('all')